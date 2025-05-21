from gui import SettingsPanel, NVDASettingsDialog,guiHelper
import config
import wx
import gui
import globalPluginHandler
import ui
import speech
import requests
import api
from scriptHandler import script
import addonHandler
from logHandler import log

try:
    addonHandler.initTranslation()
except addonHandler.AddonError:
    log.warning("Unable to init translations. This may be because the addon is running from NVDA scratchpad.")

speak= speech.speech.speak
roleSECTION = "AITranslater"
confspec = {
"translateTo": "string(default=English United States)",
"model": "integer(default=3)",
"useDialogForResults": "boolean(default=true)"}

config.conf.spec[roleSECTION] = confspec

def get_translation(text: str, announce: bool= True):
    try:
        result= translate(text)
    except Exception as e:
        result=_("{error}\n") + str(e)
    if not announce:
        return result
    if config.conf[roleSECTION]["useDialogForResults"]:
        ResultWindow(result,_("translation result"))
    else:
        speak([result])
    return result
def translate(text:str):
    if not isinstance(text, str):
        speak([_("Invalid input: not text.")])
        return
    prompt=f"""translate: 
        {text}
        to {config.conf[roleSECTION]["translateTo"]}
        give me the translated text only don't type any things except the text""".replace(" ","%20")
    model=config.conf[roleSECTION]["model"]
    endpoints = [
        f"https://blackbox-pro.bjcoderx.workers.dev/?q={prompt}",
        f"https://bj-copilot-microsoft.vercel.app/?text={prompt}",
        f"https://gpt-3-5.apis-bj-devs.workers.dev/?prompt=Hello?text={prompt}",
        f"https://gemini-1-5-flash.bjcoderx.workers.dev/?text={prompt}"
    ]
    try:
        response = requests.get(endpoints[model])
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
        self.outputCtrl = wx.TextCtrl(self,style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.outputCtrl.Bind(wx.EVT_KEY_DOWN, self.onOutputKeyDown)
        sizer.Add(self.outputCtrl, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.outputCtrl.SetValue(text)
        self.outputCtrl.SetFocus()
        self.Raise()
        self.Maximize()
        self.Show()

    def onOutputKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Destroy()
        else:
            event.Skip()
class InputText(wx.Dialog):
    def __init__(self):
        super().__init__(None,-1,title=_("input text"))
        sizer=wx.BoxSizer(wx.VERTICAL)
        panel=wx.Panel(self)
        self.textBox=wx.TextCtrl(panel,-1,style=wx.TE_MULTILINE|wx.TE_RICH)
        sizer.Add(self.textBox)
        self.translate=wx.Button(panel,-1,_("translate"))
        self.translate.Bind(wx.EVT_BUTTON,self.onTranslate)
        sizer.Add(self.translate)
        self.close= wx.Button(panel,-1,_("close"))
        self.close.Bind(wx.EVT_BUTTON,self.onClose)
        sizer.Add(self.close)
        panel.SetSizer(sizer)
        self.Show()
    def onClose(self,event):
        self.Destroy()
    def onTranslate(self,event):
        text= self.textBox.Value
        self.close.SetFocus()
        get_translation(text)

class AITranslaterSettingsPanel(SettingsPanel):
    title = _("AI translater")
    def makeSettings(self, settingsSizer):
        sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        languages = [
    "Arabic Egypt",
    "Arabic Levantine",
    "Arabic Saudi Arabia",
    "Arabic Standard",
    "Bengali Bangladesh",
    "Bengali India",
    "Chinese Cantonese",
    "Chinese Mandarin (Simplified)",
    "Chinese Mandarin (Traditional)",
    "Czech Czech Republic",
    "Danish Denmark",
    "Dutch Belgium",
    "Dutch Netherlands",
    "English Australia",
    "English Canada",
    "English India",
    "English United Kingdom",
    "English United States",
    "Finnish Finland",
    "French Belgium",
    "French Canada",
    "French France",
    "French Switzerland",
    "German Austria",
    "German Germany",
    "German Switzerland",
    "Greek Greece",
    "Hebrew Israel",
    "Hindi India",
    "Hungarian Hungary",
    "Indonesian Indonesia",
    "Italian Italy",
    "Italian Switzerland",
    "Japanese Japan",
    "Korean South Korea",
    "Malay Brunei",
    "Malay Malaysia",
    "Marathi India",
    "Norwegian Norway",
    "Persian Iran",
    "Polish Poland",
    "Portuguese Brazil",
    "Portuguese Portugal",
    "Punjabi India",
    "Punjabi Pakistan",
    "Romanian Romania",
    "Russian Russia",
    "Slovak Slovakia",
    "Spanish Argentina",
    "Spanish Colombia",
    "Spanish Mexico",
    "Spanish Spain",
    "Spanish United States",
    "Swedish Sweden",
    "Tamil India",
    "Tamil Sri Lanka",
    "Telugu India",
    "Thai Thailand",
    "Turkish Turkey",
    "Ukrainian Ukraine",
    "Urdu India",
    "Urdu Pakistan",
    "Vietnamese Vietnam"
]
        languages.sort()
        self.tlable = sHelper.addItem(wx.StaticText(self, label=_("&model"), name="ts"))
        self.sou= sHelper.addItem(wx.Choice(self, name="ts"))
        self.sou.Set([    "proAI",    "Microsoft Copilot",    "ChatGPT",    "Gemini"])
        self.tlable1 = sHelper.addItem(wx.StaticText(self, label=_("trans&late to"), name="ts1"))
        self.sou1= sHelper.addItem(wx.Choice(self, name="ts1"))
        self.sou1.Set(languages)
        self.sou.SetSelection(config.conf[roleSECTION]["model"])
        self.sou1.SetStringSelection(config.conf[roleSECTION]["translateTo"])
        self.sou2 = sHelper.addItem(wx.CheckBox(self, label=_("use &dialog for results"), name="ts2"))
        self.sou2.SetValue(config.conf[roleSECTION]["useDialogForResults"])
    def postInit(self):
        self.sou.SetFocus()
    def onSave(self):
        config.conf[roleSECTION]["model"]=self.sou.Selection
        config.conf[roleSECTION]["translateTo"]=self.sou1.StringSelection
        config.conf[roleSECTION]["useDialogForResults"]=self.sou2.Value
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        speech.speech.speak= self.speech_event
        self.record_live_speech= False
        self.lastSpoken=""
    scriptCategory= _("AI translater")
    NVDASettingsDialog.categoryClasses.append(AITranslaterSettingsPanel)
    def speech_event(self, sequence, *args, **kwargs):
        text_blocks = [    i for i in range(len(sequence))    if isinstance(sequence[i], (str, int, float, bool, type(None)))    and len(str(sequence[i])) > 1    and not str(sequence[i]).isspace()]
        self.lastSpoken="|  ".join([str(sequence[i]) for i in text_blocks])
        if self.record_live_speech:
            if len(text_blocks)>0:
                result= get_translation(self.lastSpoken, False)
                if result.startswith("{error}"):
                    self.record_live_speech= False
                result= result.split("|  ")
                for i in range(len(text_blocks)):
                    sequence[text_blocks[i]]= result[i]
        speak(sequence, *args, **kwargs)
    @script(gesture="kb:NVDA+alt+t")
    def script_textInput(self,gesture):
        self.record_live_speech= False
        InputText()
    script_textInput.__doc__= _("open translation window")
    @script(gesture="kb:NVDA+alt+c")
    def script_text_clipboard (self, gesture):
        self.record_live_speech= False
        get_translation(api.getClipData())
    script_text_clipboard.__doc__= _("Translates clipboard text ")
    @script(gesture="kb:NVDA+alt+r")
    def script_live_recording (self, gesture):
        self.record_live_speech= not self.record_live_speech
        speak([("En" if self.record_live_speech else "Dis")+ "abled recording."])
    script_live_recording.__doc__= _("Toggles translation of live text ")
    @script()
    def script_lastSpoken(self, gesture):
        self.record_live_speech= False
        if self.lastSpoken=="":
            return
        get_translation(self.lastSpoken)
    script_lastSpoken.__doc__= _("translate last spoken text")
    def terminate(self):
        self.record_live_speech= False
        speech.speech.speak= speak
        NVDASettingsDialog.categoryClasses.remove(AITranslaterSettingsPanel)
