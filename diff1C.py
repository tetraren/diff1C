
import codecs
from datetime import datetime
from os import path as os_path
from os import remove as os_remove
from os import _exit as os_exit
from os import chdir as os_chdir
from os import stat as os_stat
from pathlib import Path
from pprint import pformat
from shutil import copy
from subprocess import PIPE, Popen
import sys
import time

from ctypes import windll as ctypes_windll
import win32gui
import win32.lib.win32con as win32con

class Args:
    def __init__(self, argv) -> None:

        self.exe = None
        self.keyword_string = ""
        self.keywords = []
        self.name_base = None
        self.name_new = None
        self.name_old = None
        self.codepage = "utf8-bom"
        self.path_old = None
        self.path_base = None
        self.path_new = None
        self.path_merge = None
        self.path_log = ""

        self.diff_string = None
        self.diff_mode = False

        self.args_dict = {
            "-C": "codepage",
            "-diff" : "diff_string",
            "-exe": "exe",
            "-keywords": "keyword_string",
            "-log": "path_log",
            "-tbase": "name_base",
            "-told": "name_old",
            "-tnew": "name_new",
            "-base": "path_base",
            "-old": "path_old",
            "-new": "path_new",
            "-merge": "path_merge"
        }

        self.parse_cmdline(argv)

    def parse_cmdline(self, argv):
        lastArg = None
        cnt = 0
        for i, arg in enumerate(argv):
            if i == 0:
                continue
            
            if arg.find('-') == 0:
                lastArg = arg
                continue
            
            if lastArg != None:
                var_name = self.get_var_name(lastArg)
                if var_name == None:
                    continue
                
                setattr(self, var_name, arg)
                lastArg = None
                continue

            cnt+=1

            match cnt:
                case 1:
                    argName = "path_old"
                case 2:
                    argName = "path_base"
                case 3:
                    argName = "path_new"
                case 4:
                    argName = "path_merge"
                case _:
                    argName = None
            if argName != None:
                setattr(self, argName, arg.replace("/", "\\"))

        self.keywords = self.keyword_string.split(',') if self.keyword_string is not None else []
        self.keywords = [a for a in self.keywords if not a in [""]]

        self.exe = self._resolve_path(self.exe)
        self.path_log = self._resolve_path(self.path_log)
        self.diff_string = "1" if self.diff_string else "0"
        self.diff_mode = self.diff_string == "1"
        
        if self.diff_mode:
            self.path_merge = ""

        if not self.path_old:
            self.path_old = self.path_base
            self.name_old = self.path_base

        # FIX broken CRLF in path_merge
        self.path_merge = self.path_merge.replace("\r", "").replace("\n", "").replace("¶","")


    def get_var_name(self, cmd_arg) -> str:
        return self.args_dict.get(cmd_arg)

    def get_arg_name(self, var_name) -> str:
        values = list(self.args_dict.values())
        if var_name in values:
            return list(self.args_dict.keys())[values.index(var_name)]
        else:
            return None

    def _resolve_path(self, path):
        if path == None or path == "": return path
        if os_path.isabs(path): return path
        return str(Path(path).resolve())  

    def check_vars(self):
        #dont forget to set Processof.path_log!
        if Processor.log_path == "" and self.path_log != "":
            Processor.log_path = self.path_log

        missing = []
        for key, value in vars(self).items():
            if value is None and self.get_arg_name(key):
                missing.append(self.get_arg_name(key))

        if len(missing) > 0 :
            #EXIT
            Processor.error(f'ERROR! Parameters not defined: {", ".join(missing)}', exit = True)


class Processor:
    log_path = ""

    @classmethod
    def detect_by_bom(cls, path, default) -> str:
        with open(path, 'rb') as f:
            raw = f.read(4)    # will read less if the file is smaller
        # BOM_UTF32_LE's start is equal to BOM_UTF16_LE so need to try the former first
        for enc, boms in \
                ('utf-8-sig', (codecs.BOM_UTF8,)), \
                ('utf-32', (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)), \
                ('utf-16', (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
            if any(raw.startswith(bom) for bom in boms):
                return enc
        return default

    @classmethod
    def search_str(cls, file_path, word) -> bool:
        encoding = cls.detect_by_bom(file_path, "utf-8")
        # print("enc=",encoding)
        with open(file_path, 'r',encoding=encoding) as file:
            # read all content of a file
            content = file.read()
            # check if string present in a file
            if word in content:
                return True
            else:
                return False

    @classmethod
    def check_keywords(cls, file_path, keywords) -> bool:
        for word in keywords:
            if word != "" and cls.search_str(file_path, word):
                return True
        
        return False

    @classmethod
    def run_p4merge(cls, args : Args):
        newFile = False

        if not args.diff_mode:
            path = Path(args.path_merge)

            if not path.is_file():
                newFile = True
                with open(args.path_merge, mode='a'): pass

            cmdArgs = [args.exe,
                        "-C", args.codepage,
                        "-nl", args.name_base,
                        "-nr", args.name_new,
                        "-nb", args.name_old,
                        args.path_old,
                        args.path_base,
                        args.path_new,
                        args.path_merge
            ]
        else:
            cmdArgs = [args.exe,
                        "-C", args.codepage,
                        "-nl", args.name_base,
                        "-nr", args.name_new,
                        args.path_base,
                        args.path_new,
            ]

        process = Popen(cmdArgs, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = process.communicate()
        if err:
            msg = err.decode("utf-8").replace('\r\n', ' ')
            #EXIT
            cls.error(f'ERROR! {msg}, {pformat(cmdArgs)}', exit = True)

        if newFile and path.is_file() and os_stat(path.absolute()).st_size == 0:
            os_remove(path.absolute())

    @classmethod
    def show_dummy_window(self):
        wc = win32gui.WNDCLASS()
        wc.lpszClassName = 'test_win32gui_dummy'
        wc.style =  win32con.CS_GLOBALCLASS|win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hbrBackground = win32con.COLOR_WINDOW+1
        wc.lpfnWndProc={}
        class_atom=win32gui.RegisterClass(wc)       
        hwnd = win32gui.CreateWindow(wc.lpszClassName,
            'dummy',
            win32con.WS_CAPTION|win32con.WS_VISIBLE,
            1,1,1,1, 0, 0, 0, None)
    
        win32gui.InvalidateRect(hwnd,None,True)
        win32gui.PumpWaitingMessages()
        time.sleep(0.01)
        win32gui.DestroyWindow(hwnd)
        win32gui.UnregisterClass(wc.lpszClassName, None) 

    @classmethod
    def msgbox(cls, message, title = ""):
        ctypes_windll.user32.MessageBoxW(0, message, title, 1)        

    @classmethod
    def is_exe(cls):
        return getattr(sys, 'frozen', False)

    @classmethod
    def _log(cls, message) -> str:
        if cls.log_path == "" or not cls.log_path:
            return

        with open(cls.log_path, 'a', encoding='utf-8') as file:
            str = f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")} {message}\n'
            file.write(str)

    @classmethod
    def echo(cls, message) -> str:
        print(message)
        cls._log(message)
        return message

    @classmethod
    def error(cls, message, exit = False):
        cls._log(message)

        if cls.is_exe():
            cls.msgbox(message)
        else:
            print(message)

        if exit:
            os_exit(1)


def main():

    # if exe, change dir to executable
    #     If the application is run as a bundle, the PyInstaller bootloader
    #     extends the sys module by a flag frozen=True
    if Processor.is_exe():
        os_chdir(os_path.dirname(sys.executable))
        
    args = Args(sys.argv)
    Processor.log_path = args.path_log
    args.check_vars()

    if not args.diff_mode:
        if len(args.keywords) > 0 and not Processor.check_keywords(args.path_base, args.keywords) \
                                  and not Processor.check_keywords(args.path_new, args.keywords):
            Processor.echo(f'"{args.keyword_string}" NOT MATCHED, COPY! {args.name_base.replace("(Основная конфигурация)","")} => Copy [{args.path_new}] to [{args.path_merge}]')
            copy(args.path_new, args.path_merge)
            Processor.show_dummy_window() #little hack to get focus (1c freeses instead)
        else:
            #-C utf8-bom -nl %baseCfgTitle -nr %secondCfgTitle -nb %oldVendorCfgTitle %oldVendorCfg %baseCfg %secondCfg %merged
            Processor.echo(f'"{args.keyword_string}" MATCHED, DIFF! {args.name_base.replace("(Основная конфигурация)","")} => DIFF [{args.path_old}]  [{args.path_base}]  [{args.path_new}] to [{args.path_merge}]')
            Processor.run_p4merge(args)

    else:
        Processor.run_p4merge(args)

if __name__ == "__main__":
    main()



