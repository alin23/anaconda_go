
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import os
import time
import sublime
from subprocess import PIPE

from anaconda_go.lib.plugin import typing as tp
from anaconda_go.lib.plugin import create_subprocess
from anaconda_go.lib.helpers import get_settings, active_view


class GolangDetector:
    """Detect the local golang installation (if any)
    """

    _detected = False
    GOROOT = None  # type: str
    GOPATH = None  # type: str
    CGO_ENABLED = None  # type: bool

    def __call__(self):
        start = time.time()
        if self._detect_in_configuration():
            self._detected = True
        elif self._detect_in_environment():
            self._detected = True

        if not self._detected and self._detect_in_shell():
            self._detected = True

        if self._detected:
            print('anaconda_go: finished detecting environment in {}s'.format(
                time.time() - start
            ))
        else:
            sublime.error_message(
                'anaconda_go has been unable to determine the following '
                'required environment variables:\n'
                '\tGOROOT {}\n\tGOPATH {}\n\tCGO_ENABLED {}\n\n'
                'anaconda_go can\'t work without those variables, that means '
                'that the plugin is not going to work out of the box and you '
                'will provide the correct values for these variables in any '
                'configuration level (project settings or anaconda_go settings'
                ')\n\n(set the option `go_detector_silent` as `true` if you '
                'do not want to see this warning again)'
                ''.format(self.GOROOT, self.GOPATH, self.CGO_ENABLED)
            )

        return (self.GOROOT, self.GOPATH, self.CGO_ENABLED)

    @property
    def go_binary(self) -> str:
        """Return back the go binary location if Go is detected
        """

        if self._detected:
            return os.path.join(self.GOROOT, 'bin', 'go')

    @property
    def go_version(self) -> str:
        """Return back the version of the go compiler/runtime
        """

        if self._detected:
            args = '{} version'.format(self.go_binary).split()
            go = create_subprocess(args, stdout=PIPE)
            output, _ = go.communicate()

            try:
                return output.split()[2]
            except:
                pass

        return ""

    def _detect_in_configuration(self) -> bool:
        """Detect and validate Go parameters in configuration
        """

        view = active_view()

        goroot = get_settings(view, 'anaconda_go_GOROOT', '')
        gopath = get_settings(view, 'anaconda_go_GOPATH', '')
        if goroot and gopath:
            if os.path.exists(os.path.join(goroot, 'bin', 'go')):
                self.GOROOT = goroot
                self.GOPATH = gopath
                return True

        return False

    def _detect_in_environment(self) -> bool:
        """Detect Go parameters in the inheritted shell environemnt vars
        """

        environ = os.environ
        self.GOROOT = environ.get('GOROOT')
        self.GOPATH = environ.get('GOPATH')
        self.CGO_ENABLED = self._normalize_cgo(environ.get('CGO_ENABLED'))

        if self.GOROOT is None or self.GOPATH is None:
            return False

        return True

    def _detect_in_shell(self) -> bool:
        """Detect Go parameters using the shell directly
        """

        if sublime.platform() == 'windows':
            return self._detect_in_windows_shell()

        return self._detect_in_unix_shell()

    def _detect_in_windows_shell(self) -> bool:
        """Detect Go parameters in windows shell (normally cmd)
        """

        shell = os.environ.get('COMSPEC', 'cmd')
        self._spawn_processes([shell, '/C'])
        if self.GOROOT is None or self.GOPATH is None:
            return False

        return True

    def _detect_in_unix_shell(self) -> bool:
        """Deect Go parameters in unix shell (normally sh)
        """

        shell = os.environ.get('SHELL', 'sh')
        self._spawn_processes([shell, '-l', '-c'])
        if self.GOROOT is None or self.GOPATH is None:
            return False

        return True

    def _spawn_processes(self, args: tp.List) -> None:
        """Spawn a shell process and ask for go environment variables
        """

        for var in ['GOROOT', 'GOPATH', 'CGO_ENABLED']:
            targs = args + ['go env {}'.format(var)]
            try:
                proc = create_subprocess(targs, stdout=PIPE, stderr=PIPE)
            except Exception as err:
                print('anaconda_go: go binary is not in your PATH:', err)
                return

            output, _ = proc.communicate()
            if output != '':
                if var == 'CGO_ENABLED':
                    self.CGO_ENABLED = self._normalize_cgo(output)
                else:
                    setattr(self, var, output.decode('utf8').strip())

    def _normalize_cgo(self, cgo: tp.Union[str, None]) -> bool:
        """Set CGO_ENABLED to False if is not set
        """

        if cgo is None:
            return False
        return bool(int(cgo))