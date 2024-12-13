from gui import SettingsPanel, NVDASettingsDialog,guiHelper
import config
import wx
import gui
import globalPluginHandler
import ui
import requests
import api
from scriptHandler import script
import addonHandler
addonHandler.initTranslation()

roleSECTION = "AITranslater"
confspec = {
"translateTo": "string(default=German Germany)",
"model": "integer(default=0)"}

config.conf.spec[roleSECTION] = confspec
def translate(text:str):
    prompt=f"""translate: 
        {text}
        to {config.conf[roleSECTION]["translateTo"]}
        give me the translated text only don't type any things except the text"""

    apiLlama="LL-7GSSOuFGJRrDTxot9HwuANRqUqFchg1cjchgx9qTehfksBKp9OIei0JQoLnVpHKs"
    apiGemini="AIzaSyDYeLxp7Jp5qSypbVBPy9v_XYmz7Sc1qfs"
    model=config.conf[roleSECTION]["model"]
    if model==0:
        response=requests.get("https://darkness.ashlynn.workers.dev/chat/?model=gpt-4o-mini&prompt=" + prompt.replace(" ","%22"))
        path=0
    elif model==1:
        api_request_json = {
  "model": "llama3.1-405b",
"max_tokens":3000,
  "messages": [
    {"role": "user", "content": prompt},
  ]
}
        response=requests.post("https://api.llama-api.com/chat/completions",headers={'Authorization': 'Bearer ' + apiLlama,'Content-Type': 'application/json',},json=api_request_json)
        path=1
    elif model==2:
        headrs={
            'Content-Type':'application/json',
        }
        data={"contents":[{"parts":[{"text":prompt}]}]}
        response=requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + apiGemini,headers=headrs,json=data)
        path=2
    if response.status_code==200:
        if path==0:
            result=response.json()["response"]
        elif path==1:
            result=response.json()["choices"][0]["message"]["content"]
        elif path==2:
            result=response.json()['candidates'][0]["content"]["parts"][0]["text"]
    else:
        result="error"
    return result

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
            self.Close()
        event.Skip()
class InputText(wx.Dialog):
    def __init__(self):
        super().__init__(None,-1,title=_("input text"))
        sizer=wx.BoxSizer(wx.VERTICAL)
        panel=wx.Panel(self)
        self.textBox=wx.TextCtrl(panel,-1,style=wx.TE_MULTILINE|wx.TE_RICH)
        sizer.Add(self.textBox)
        self.translate=wx.Button(panel,-1,_("translate"))
        sizer.Add(self.translate)
        panel.SetSizer(sizer)
        self.Bind(wx.EVT_BUTTON,self.onTranslate)
        self.Show()
    def onOutputKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        event.Skip()
    def onTranslate(self,event):
        try:
            result=translate(self.textBox.Value)
        except Exception as e:
            result=_("error ") + str(e)
        self.Destroy()
        ResultWindow(result,_("translation result"))

class AITranslaterSettingsPanel(SettingsPanel):
    title = _("AI translater")
    def makeSettings(self, settingsSizer):
        sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        languages = [
    "English United States",
    "English United Kingdom",
    "English Australia",
    "English Canada",
    "English India",
    "Spanish Spain",
    "Spanish Mexico",
    "Spanish Argentina",
    "Spanish Colombia",
    "Spanish United States",
    "French France",
    "French Canada",
    "French Belgium",
    "French Switzerland",
    "Portuguese Portugal",
    "Portuguese Brazil",
    "German Germany",
    "German Austria",
    "German Switzerland",
    "Arabic Standard",
    "Arabic Egypt",
    "Arabic Saudi Arabia",
    "Arabic Levantine",
    "Chinese Mandarin (Simplified)",
    "Chinese Mandarin (Traditional)",
    "Chinese Cantonese",
    "Dutch Netherlands",
    "Dutch Belgium",
    "Russian Russia",
    "Italian Italy",
    "Italian Switzerland",
    "Japanese Japan",
    "Korean South Korea",
    "Hindi India",
    "Swedish Sweden",
    "Norwegian Norway",
    "Danish Denmark",
    "Finnish Finland",
    "Greek Greece",
    "Turkish Turkey",
    "Polish Poland",
    "Hebrew Israel",
    "Indonesian Indonesia",
    "Malay Malaysia",
    "Malay Brunei",
    "Thai Thailand",
    "Vietnamese Vietnam",
    "Bengali Bangladesh",
    "Bengali India",
    "Punjabi India",
    "Punjabi Pakistan",
    "Tamil India",
    "Tamil Sri Lanka",
    "Telugu India",
    "Marathi India",
    "Urdu Pakistan",
    "Urdu India"
]
        languages.sort()
        self.tlable = sHelper.addItem(wx.StaticText(self, label=_("model"), name="ts"))
        self.sou= sHelper.addItem(wx.Choice(self, name="ts"))
        self.sou.Set(["chatgpt","llama","gemini"])
        self.tlable1 = sHelper.addItem(wx.StaticText(self, label=_("translate to"), name="ts1"))
        self.sou1= sHelper.addItem(wx.Choice(self, name="ts1"))
        self.sou1.Set(languages)
        self.sou.SetSelection(config.conf[roleSECTION]["model"])
        self.sou1.SetStringSelection(config.conf[roleSECTION]["translateTo"])
    def postInit(self):
        self.sou.SetFocus()
    def onSave(self):
        config.conf[roleSECTION]["model"]=self.sou.Selection
        config.conf[roleSECTION]["translateTo"]=self.sou1.StringSelection
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory= _("AI translater")
    NVDASettingsDialog.categoryClasses.append(AITranslaterSettingsPanel)
    @script(gesture="kb:NVDA+alt+t")
    def script_textInput(self,gesture):
        InputText()
    script_textInput.__doc__= _("open translation window")
    @script(gesture="kb:NVDA+alt+c")
    def script_hi (self, gesture):
        try:
            result=translate(api.getClipData())
        except Exception as e:
            result=_("error ") + str(e)
        ResultWindow(result,_("translation result"))
    script_hi.__doc__= _("Translates clipboard text ")
    def terminate(self):
        NVDASettingsDialog.categoryClasses.remove(AITranslaterSettingsPanel)