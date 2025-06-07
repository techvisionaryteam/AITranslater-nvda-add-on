import threading
import gui
from gui import SettingsPanel, NVDASettingsDialog, guiHelper
import config
import wx
import globalPluginHandler
import ui
import speech
import requests
import api
from scriptHandler import script
import addonHandler
from logHandler import log
import pyperclip
import uuid

try:
    addonHandler.initTranslation()
except addonHandler.AddonError:
    log.warning("Unable to init translations. This may be because the addon is running from NVDA scratchpad.")

speak = speech.speech.speak
roleSECTION = "AITranslater"
confspec = {
    "translateTo": "string(default=English United States)",
    "model": "integer(default=3)",
    "useDialogForResults": "boolean(default=true)"
}

config.conf.spec[roleSECTION] = confspec

def get_translation(text: str, announce: bool = True):
    try:
        result = translate(text)
    except Exception as e:
        result = _("{error}\n") + str(e)
    if not announce:
        return result
    if config.conf[roleSECTION]["useDialogForResults"]:
        ResultWindow(result, _("Translation Result"))
    else:
        speak([result])
    return result

def translate(text: str):
    if not isinstance(text, str):
        speak([_("Invalid input: not text.")])
        return
    prompt = f"""translate: 
        {text}
        to {config.conf[roleSECTION]["translateTo"]}
        give me the translated text only don't type any things except the text""".replace(" ", "%20")
    model = config.conf[roleSECTION]["model"]
    endpoints = [
        f"https://blackbox-pro.bjcoderx.workers.dev/?q={prompt}",
        f"https://bj-copilot-microsoft.vercel.app/?text={prompt}",
        f"https://gpt-3-5.apis-bj-devs.workers.dev/?prompt=Hello?text={prompt}",
        f"https://gemini-1-5-flash.bjcoderx.workers.dev/?text={prompt}"
    ]
    try:
        response = requests.get(endpoints[model], timeout=10)
        response.raise_for_status()
        data = response.json()
        if model == 0:
            return data["data"]["result"]
        elif model == 1:
            return data["answer"]
        elif model == 2:
            return data["reply"]
        elif model == 3:
            return data["text"]
        else:
            return "Invalid model index."
    except Exception as e:
        return f"Error: {str(e)}"

class ResultWindow(wx.Dialog):
    def __init__(self, text, title):
        super(ResultWindow, self).__init__(gui.mainFrame, title=title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.output_label = wx.StaticText(self, label=_("Translated text:"))
        sizer.Add(self.output_label, flag=wx.ALL, border=5)
        self.outputCtrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.outputCtrl.Bind(wx.EVT_KEY_DOWN, self.onOutputKeyDown)
        sizer.Add(self.outputCtrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.copy_button = wx.Button(self, label=_("Copy"))
        self.copy_button.Bind(wx.EVT_BUTTON, self.onCopy)
        button_sizer.Add(self.copy_button, flag=wx.ALL, border=5)
        self.back_button = wx.Button(self, label=_("Back"))
        self.back_button.Bind(wx.EVT_BUTTON, self.onBack)
        button_sizer.Add(self.back_button, flag=wx.ALL, border=5)
        self.exit_button = wx.Button(self, label=_("Exit"))
        self.exit_button.Bind(wx.EVT_BUTTON, self.onExit)
        button_sizer.Add(self.exit_button, flag=wx.ALL, border=5)
        sizer.Add(button_sizer, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.outputCtrl.SetValue(text)
        self.outputCtrl.SetFocus()
        self.Raise()
        self.Maximize()
        self.Show()

    def onOutputKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.onBack(event)
        else:
            event.Skip()

    def onCopy(self, event):
        pyperclip.copy(self.outputCtrl.GetValue())
        speak([_("Text copied to clipboard.")])

    def onBack(self, event):
        self.Destroy()
        InputText()

    def onExit(self, event):
        self.Destroy()
        wx.GetApp().ExitMainLoop()

class InputText(wx.Dialog):
    def __init__(self):
        super().__init__(None, -1, title=_("Input Text"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self)
        self.input_label = wx.StaticText(panel, label=_("Enter the text to translate:"))
        sizer.Add(self.input_label, flag=wx.ALL, border=5)
        self.textBox = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_RICH)
        sizer.Add(self.textBox, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.translate_button = wx.Button(panel, label=_("Translate"))
        self.translate_button.Bind(wx.EVT_BUTTON, self.onTranslate)
        button_sizer.Add(self.translate_button, flag=wx.ALL, border=5)
        self.clear_button = wx.Button(panel, label=_("Clear"))
        self.clear_button.Bind(wx.EVT_BUTTON, self.onClear)
        button_sizer.Add(self.clear_button, flag=wx.ALL, border=5)
        self.exit_button = wx.Button(panel, label=_("Exit"))
        self.exit_button.Bind(wx.EVT_BUTTON, self.onExit)
        button_sizer.Add(self.exit_button, flag=wx.ALL, border=5)
        sizer.Add(button_sizer, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        panel.SetSizer(sizer)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.textBox.SetFocus()
        self.Show()

    def onClear(self, event):
        if not self.textBox.GetValue():
            gui.messageBox(_("No text to clear."), _("Information"), wx.OK | wx.ICON_INFORMATION)
            return
        self.textBox.SetValue("")
        self.textBox.SetFocus()

    def onTranslate(self, event):
        text = self.textBox.GetValue()
        if not text:
            gui.messageBox(_("Please enter text to translate."), _("Error"), wx.OK | wx.ICON_ERROR)
            return
        self.translate_button.Enable(False)
        threading.Thread(target=self.translate_in_background, args=(text,)).start()

    def translate_in_background(self, text):
        try:
            result = get_translation(text, announce=False)
            wx.CallAfter(self.onTranslationComplete, result)
        except Exception as e:
            wx.CallAfter(self.onTranslationError, str(e))

    def onTranslationComplete(self, result):
        self.translate_button.Enable(True)
        if config.conf[roleSECTION]["useDialogForResults"]:
            self.Destroy()
            ResultWindow(result, _("Translation Result"))
        else:
            speak([result])

    def onTranslationError(self, error):
        self.translate_button.Enable(True)
        gui.messageBox(_("Translation failed: {error}").format(error=error), _("Error"), wx.OK | wx.ICON_ERROR)

    def onExit(self, event):
        self.Destroy()
        wx.GetApp().ExitMainLoop()

class AITranslaterSettingsPanel(SettingsPanel):
    title = _("AI Translator Settings")
    def makeSettings(self, settingsSizer):
        sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        languages = [
            "Arabic Egypt", "Arabic Levantine", "Arabic Saudi Arabia", "Arabic Standard",
            "Bengali Bangladesh", "Bengali India", "Chinese Cantonese", "Chinese Mandarin (Simplified)",
            "Chinese Mandarin (Traditional)", "Czech Czech Republic", "Danish Denmark",
            "Dutch Belgium", "Dutch Netherlands", "English Australia", "English Canada",
            "English India", "English United Kingdom", "English United States", "Finnish Finland",
            "French Belgium", "French Canada", "French France", "French Switzerland",
            "German Austria", "German Germany", "German Switzerland", "Greek Greece",
            "Hebrew Israel", "Hindi India", "Hungarian Hungary", "Indonesian Indonesia",
            "Italian Italy", "Italian Switzerland", "Japanese Japan", "Korean South Korea",
            "Malay Brunei", "Malay Malaysia", "Marathi India", "Norwegian Norway",
            "Persian Iran", "Polish Poland", "Portuguese Brazil", "Portuguese Portugal",
            "Punjabi India", "Punjabi Pakistan", "Romanian Romania", "Russian Russia",
            "Slovak Slovakia", "Spanish Argentina", "Spanish Colombia", "Spanish Mexico",
            "Spanish Spain", "Spanish United States", "Swedish Sweden", "Tamil India",
            "Tamil Sri Lanka", "Telugu India", "Thai Thailand", "Turkish Turkey",
            "Ukrainian Ukraine", "Urdu India", "Urdu Pakistan", "Vietnamese Vietnam"
        ]
        languages.sort()
        self.model_label = sHelper.addItem(wx.StaticText(self, label=_("Select translation &model:")))
        self.model_choice = sHelper.addItem(wx.Choice(self, name="model_choice"))
        self.model_choice.Set(["proAI", "Microsoft Copilot", "ChatGPT", "Gemini"])
        self.language_label = sHelper.addItem(wx.StaticText(self, label=_("Select target &language:")))
        self.language_choice = sHelper.addItem(wx.Choice(self, name="language_choice"))
        self.language_choice.Set(languages)
        self.dialog_label = sHelper.addItem(wx.StaticText(self, label=_("Use &dialog for translation results:")))
        self.dialog_checkbox = sHelper.addItem(wx.CheckBox(self, label=_("Use dialog for results")))
        self.model_choice.SetSelection(config.conf[roleSECTION]["model"])
        self.language_choice.SetStringSelection(config.conf[roleSECTION]["translateTo"])
        self.dialog_checkbox.SetValue(config.conf[roleSECTION]["useDialogForResults"])

    def postInit(self):
        self.model_choice.SetFocus()

    def onSave(self):
        config.conf[roleSECTION]["model"] = self.model_choice.GetSelection()
        config.conf[roleSECTION]["translateTo"] = self.language_choice.GetStringSelection()
        config.conf[roleSECTION]["useDialogForResults"] = self.dialog_checkbox.GetValue()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        speech.speech.speak = self.speech_event
        self.record_live_speech = False
        self.lastSpoken = ""
        NVDASettingsDialog.categoryClasses.append(AITranslaterSettingsPanel)

    scriptCategory = _("AI Translator")

    def speech_event(self, sequence, *args, **kwargs):
        text_blocks = [i for i in range(len(sequence)) if isinstance(sequence[i], (str, int, float, bool, type(None))) and len(str(sequence[i])) > 1 and not str(sequence[i]).isspace()]
        self.lastSpoken = "|  ".join([str(sequence[i]) for i in text_blocks])
        if self.record_live_speech:
            if len(text_blocks) > 0:
                result = get_translation(self.lastSpoken, False)
                if result.startswith("{error}"):
                    self.record_live_speech = False
                result = result.split("|  ")
                for i in range(len(text_blocks)):
                    sequence[text_blocks[i]] = result[i]
        speak(sequence, *args, **kwargs)

    @script(gesture="kb:NVDA+alt+t")
    def script_textInput(self, gesture):
        self.record_live_speech = False
        InputText()
    script_textInput.__doc__ = _("Open translation window")

    @script(gesture="kb:NVDA+alt+c")
    def script_text_clipboard(self, gesture):
        self.record_live_speech = False
        get_translation(api.getClipData())
    script_text_clipboard.__doc__ = _("Translates clipboard text")

    @script(gesture="kb:NVDA+alt+r")
    def script_live_recording(self, gesture):
        self.record_live_speech = not self.record_live_speech
        speak([("En" if self.record_live_speech else "Dis") + "abled recording."])
    script_live_recording.__doc__ = _("Toggles translation of live text")

    @script()
    def script_lastSpoken(self, gesture):
        self.record_live_speech = False
        if self.lastSpoken == "":
            return
        get_translation(self.lastSpoken)
    script_lastSpoken.__doc__ = _("Translate last spoken text")

    def terminate(self):
        self.record_live_speech = False
        speech.speech.speak = speak
        NVDASettingsDialog.categoryClasses.remove(AITranslaterSettingsPanel)
