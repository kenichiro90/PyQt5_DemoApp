import copy, glob, os, sys, time, traceback
from PyQt5.QtCore import (Qt, QThreadPool, QRunnable, pyqtSignal, pyqtSlot, 
                        QObject, QDate)
from PyQt5.QtWidgets import (QTabWidget, QWidget, QVBoxLayout, QFileDialog, 
                            QGroupBox, QFormLayout, QPushButton, QLineEdit, 
                            QCheckBox, QHBoxLayout, QMessageBox, QApplication, 
                            QMainWindow, QProgressBar)
from DemoApp_UI import Ui_DemoApp
import globalParams


class DemoApp(QWidget):
    # -------------------------------------------------------------------------
    # シグナルの初期化
    # -------------------------------------------------------------------------
    sig_progressBar_value = pyqtSignal(int)
    sig_error_message = pyqtSignal(object)

    def __init__(self, parent=None):

        # ---------------------------------------------------------------------
        # ウィジェットの初期化
        # ---------------------------------------------------------------------
        super(DemoApp, self).__init__(parent)
        self.ui = Ui_DemoApp()
        self.ui.setupUi(self)
        # ---------------------------------------------------------------------
        # シグナルとスロットの接続
        #   参考にしたサイト
        #     http://t2y.hatenablog.jp/entry/20100914/1284402024
        # ---------------------------------------------------------------------
        self.threadPool = QThreadPool()
        self.sig_progressBar_value.connect(self.refresh_progressBar)
        self.sig_error_message.connect(self.display_sig_error_message)
        # ---------------------------------------------------------------------
        # フラグの初期化
        # ---------------------------------------------------------------------
        self.mainFlag = False
        self.errorFlag = False

    @pyqtSlot(int)
    def refresh_progressBar(self, int):

        # ---------------------------------------------------------------------
        # プログレスバーの値を更新する
        # ---------------------------------------------------------------------
        self.ui.progressBar.setValue(int)

    def watch_progressBar_status(self):

        # ---------------------------------------------------------------------
        # カウントしたファイル数に達するまで、ループし続ける
        # ---------------------------------------------------------------------
        while (globalParams.fileCounter < globalParams.fileNum and 
                                                self.errorFlag != True):
            # シグナルを受け取ったら、プログレスバーの値を更新する
            time.sleep(0.2)
            self.sig_progressBar_value.emit(globalParams.fileCounter)

    def location_on_the_screen(self, xPos, yPos):

        # ---------------------------------------------------------------------
        # 画面の左上へウィンドウを移動する
        # ---------------------------------------------------------------------
        self.move(xPos, yPos)

    def showInputFolderDialog(self):

        # ---------------------------------------------------------------------
        # 入力フォルダ選択用ダイアログの表示
        # ---------------------------------------------------------------------
        self.inputFd = QFileDialog()
        self.inputFp = self.inputFd.getExistingDirectory()
        if self.inputFd:
            self.ui.inputFolderLineEdit.setText(self.inputFp)
        elif self.inputFd == "":
            pass

    def showOutputFolderDialog(self):

        # ---------------------------------------------------------------------
        # 出力フォルダ選択用ダイアログの表示
        # ---------------------------------------------------------------------
        self.outputFd = QFileDialog()
        self.outputFp = self.outputFd.getExistingDirectory()
        if self.outputFd:
            self.ui.outputFolderLineEdit.setText(self.outputFp)
        elif self.outputFd == "":
            pass

    def readConfigFileDialog(self):

        # ---------------------------------------------------------------------
        # Configファイル選択用ダイアログの表示
        # ---------------------------------------------------------------------
        self.readConfigFd = QFileDialog()
        self.readConfigFp = self.readConfigFd.getOpenFileName(
                        self, u"ファイルを開く", "", u"Configファイル(*.ini)")
        print(self.readConfigFp)
        # ---------------------------------------------------------------------
        # ConfigファイルのパースとGUIへの反映
        # ---------------------------------------------------------------------
        if self.readConfigFp[0]:
            self.parseConfigFile()
            self.setFromConfigFile()
            QMessageBox.information(self, "Message", 
                                    u"設定内容をConfigファイルから読み込みました")
        elif self.readConfigFp[0] == "":
            pass

    def writeConfigFileDialog(self):

        # ---------------------------------------------------------------------
        # Configファイル選択用ダイアログの表示
        # ---------------------------------------------------------------------
        self.writeConfigFd = QFileDialog()
        self.writeConfigFp = self.writeConfigFd.getSaveFileName(
                        self, u"名前を付けて保存", "", u"Configファイル(*.ini)")
        # ---------------------------------------------------------------------
        # GUIの内容をConfigファイルに書き込む
        # ---------------------------------------------------------------------
        if self.writeConfigFp[0]:
            self.setToConfigFile()
            self.ui.configFileLineEdit.setText(self.writeConfigFp[0])
            QMessageBox.information(self, "Message", 
                                    u"設定内容をConfigファイルに書き込みました")
        elif self.writeConfigFp[0] == "":
            pass

    def setToConfigFile(self):

        # ---------------------------------------------------------------------
        # Configファイルへ書き込む動作を記述する
        # ---------------------------------------------------------------------
        pass

    def parseConfigFile(self):

        # ---------------------------------------------------------------------
        # Configファイルの内容をパースする動作を記述する
        # ---------------------------------------------------------------------
        pass

    def setFromConfigFile(self):

        # ---------------------------------------------------------------------
        # Configファイルから読み込む動作を記述する
        # ---------------------------------------------------------------------
        pass

    def update_status_mainAnalysis(self):

        # ---------------------------------------------------------------------
        # finishedシグナルを受け取った後に、実行される内容
        # ---------------------------------------------------------------------
        if self.errorFlag != True:
            QMessageBox.information(self, "Message", u"処理が完了しました。")
        self.ui.analyzerStateLabel.setText(u"待機中")
        self.ui.progressBar.setValue(0)
        # ---------------------------------------------------------------------
        # 全スレッドを開放する
        # ---------------------------------------------------------------------
        self.threadPool.releaseThread()

    def multiThread_runMainAnalysis(self):

        # ---------------------------------------------------------------------
        # グローバル変数の初期化
        # ---------------------------------------------------------------------
        globalParams.fileNum = 0
        globalParams.fileCounter = 0
        # ---------------------------------------------------------------------
        # Thread(解析プログラム)の初期化
        # ---------------------------------------------------------------------
        worker = Worker(self.runMainModule)
        worker.signals.finished.connect(self.update_status_mainAnalysis)
        # ---------------------------------------------------------------------
        # Thread(プログレスバー更新用メソッド)の初期化
        # ---------------------------------------------------------------------
        worker2 = Worker(self.watch_progressBar_status)
        # ---------------------------------------------------------------------
        # 解析を実行するファイル数のカウント & プログレスバーの初期化
        # ---------------------------------------------------------------------
        try:
            self.countInputFiles()
            self.ui.progressBar.setRange(0, int(globalParams.fileNum))
            # ---------------------------------------------------------------------
            # Threadの実行
            # ---------------------------------------------------------------------
            self.threadPool.start(worker)
            self.threadPool.start(worker2)
        except:
            pass

    def singleThread_runMainAnalysis(self):

        # ---------------------------------------------------------------------
        # グローバル変数の初期化
        # ---------------------------------------------------------------------
        globalParams.fileNum = 0
        globalParams.fileCounter = 0
        # ---------------------------------------------------------------------
        # 解析を実行するファイル数のカウント & プログレスバーの初期化
        # ---------------------------------------------------------------------
        try:
            self.countInputFiles()
            self.ui.progressBar.setRange(0, int(globalParams.fileNum))
            # ---------------------------------------------------------------------
            # main処理の実行
            # ---------------------------------------------------------------------
            self.runMainModule()
        except:
            pass
        
    @pyqtSlot(object)
    def display_sig_error_message(self, object):

        # ---------------------------------------------------------------------
        # エラー種別に応じたメッセージを出力する
        # ---------------------------------------------------------------------
        if type(object) == ValueError:
            QMessageBox.warning(self, "Message", 
                u"不正な値が入力されました。\n\n正しい値を入力してください。")
        elif type(object) == FileNotFoundError:
            QMessageBox.warning(self, "Message", 
                u"ファイルが見つかりません。")
        elif type(object) == PermissionError:
            QMessageBox.warning(self, "Message", 
                u"開いているファイルを閉じてください。")
        else:
            print("Error Type: {0}".format(object))
            QMessageBox.critical(self, "Message", 
                u"予期せぬエラーが発生しました。\n\n設定したパラメータが正しいか確認してください。")
        # ---------------------------------------------------------------------
        # 全スレッドの開放 & フラグとプログレスバーの初期化
        # ---------------------------------------------------------------------
        self.threadPool.releaseThread()
        self.errorFlag = False
        self.ui.analyzerStateLabel.setText(u"待機中")
        self.ui.progressBar.setValue(0)

    def countInputFiles(self):

        # ---------------------------------------------------------------------
        # グローバル変数の初期化
        # ---------------------------------------------------------------------
        if (self.ui.inputFolderLineEdit.text() == 
                                "入力フォルダの絶対パスを指定してください" or 
                                self.ui.inputFolderLineEdit.text() == ""):
            self.display_sig_error_message(ValueError)
        else:
            filePath = glob.glob(self.ui.inputFolderLineEdit.text() + "/*.*")
            globalParams.fileNum = len(filePath)

    def runMainModule(self):

        # ---------------------------------------------------------------------
        # アプリケーションの状態表示を更新する
        # ---------------------------------------------------------------------
        self.ui.analyzerStateLabel.setText(u"実行中")
        QApplication.processEvents()
        # ---------------------------------------------------------------------
        # Configファイルの内容を、GUI上に表示されている内容で上書きする
        # ---------------------------------------------------------------------
        self.writeConfigFp = []
        self.writeConfigFp.append(self.ui.configFileLineEdit.text())
        self.setToConfigFile()
        # ---------------------------------------------------------------------
        # Mainモジュールの実行
        # ---------------------------------------------------------------------
        try:
            # -----------------------------------------------------------------
            # 例外テスト用
            # -----------------------------------------------------------------            
            if self.ui.valueErrorCheckBox.isChecked() == True:
                raise ValueError
            elif self.ui.fileNotFoundErrorCheckBox.isChecked() == True:
                raise FileNotFoundError
            elif self.ui.permissionErrorCheckBox.isChecked() == True:
                raise PermissionError
            else:
                # -------------------------------------------------------------
                # 例外テスト用のチェックボックスに、チェックが付いてない場合は、
                # 通常通りに処理を実行する
                # -------------------------------------------------------------                
                sA = SluggishActionClass(globalParams.fileNum)
                mainFlag = sA.main()
                if mainFlag == True:
                    pass
        except ValueError as e:
            self.send_error_signal(e)
        except FileNotFoundError as e:
            self.send_error_signal(e)
        except PermissionError as e:
            self.send_error_signal(e)
        except:
            # Tracebackの内容をシグナルとして送る
            e = traceback.format_exc()
            self.send_error_signal(e)

    def send_error_signal(self, e):

        # ---------------------------------------------------------------------
        # エラー用フラグを上げる
        # ---------------------------------------------------------------------
        self.errorFlag = True
        # ---------------------------------------------------------------------
        # エラー内容をシグナルとして送る
        # ---------------------------------------------------------------------
        self.sig_error_message.emit(e)


class SluggishActionClass():
    def __init__(self, fileNum):

        # ---------------------------------------------------------------------
        # 値の初期化
        # ---------------------------------------------------------------------
        self.fileNum = fileNum

    def main(self):

        for _ in range(self.fileNum):
            # 1秒待つ動作を実行する
            time.sleep(1)
            globalParams.fileCounter += 1
            print("{0} of {1} has analyzed.".format(
                            globalParams.fileCounter, globalParams.fileNum))
        else:
            return True


# -----------------------------------------------------------------------------
# マルチスレッド処理用クラス(QThreadPool)
#   参考サイト
#     https://martinfitzpatrick.name/article/multithreading-pyqt-applications-with-qthreadpool/
# -----------------------------------------------------------------------------
class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:
      finished  :       No data
      error     :       `tuple` (exctype, value, traceback.format_exc())
      result    :       `object` data returned from processing, anything
      progress  :       `int` indicating % progress
    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback:    The function callback to run on this worker thread.
                        Supplied args and kwargs wil be passed through to the runner.
    :type callback:     function
    :param args:        Arguments to pass to the callback function
    :param kwargs:      Keywords to pass to the callback function
    '''
    def __init__(self, fn, *args, **kwargs):

        # Initialize
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):

        # Retrive args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)    # Return the result of the processing
        finally:
            self.signals.finished.emit()        # Done


# -----------------------------------------------------------------------------
# これ以降は実行用コード
# -----------------------------------------------------------------------------
def main():

    # -------------------------------------------------------------------------
    # アプリケーションの初期化
    # -------------------------------------------------------------------------
    app = QApplication(sys.argv)
    # -------------------------------------------------------------------------
    # ウィンドウのスタイル定義
    #   "windows"       : Windowsクラシックスタイル
    #   "windowsvista"  : Vistaスタイル
    #   "fusion"        : Qtオリジナル
    #   "macintosh"     : Macスタイル
    # -------------------------------------------------------------------------
    app.setStyle("fusion")
    # -------------------------------------------------------------------------
    # ウィンドウの生成 & 初期位置への移動
    # -------------------------------------------------------------------------
    window = DemoApp()
    window.location_on_the_screen(100, 100)
    # -------------------------------------------------------------------------
    # ウィンドウの表示 & 終了時動作の宣言
    # -------------------------------------------------------------------------
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
