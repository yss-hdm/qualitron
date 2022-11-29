import clr
import wpf
import os.path as op
import revitron
from System import Windows
from pyrevit import forms
from pyrevit import framework
from pyrevit.forms import WPFWindow
from qualitron.event import EventManager
clr.AddReference('System')
from System.Windows.Media import BrushConverter





class ColorSwitchWindow(forms.CommandSwitchWindow):
    """
    Extended form to select from a list of command options.

    Args:
        context (list[str]): list of command options to choose from
        switches (list[str]): list of on/off switches
        message (str): window title message
        config (dict): dictionary of config dicts for options or switches
        recognize_access_key (bool): recognize '_' as mark of access key
    """

    def __init__(self,
                context,
                xamlFilesDir,
                xamlSource,
                title,
                width,
                height,
                **kwargs):
        """
        Initialize user input window.
        """
        WPFWindow.__init__(self,
                           op.join(xamlFilesDir, xamlSource),
                           handle_esc=True)
        self.Title = title or 'pyRevit'
        self.Width = width
        self.Height = height

        self._context = context
        self.response = None

        # parent window?
        owner = kwargs.get('owner', None)
        if owner:
            # set wpf windows directly
            self.Owner = owner
            self.WindowStartupLocation = \
                framework.Windows.WindowStartupLocation.CenterOwner

        self._setup(**kwargs)

    def colorButtons(self):
        """
        Sets the background color for all buttons according to the corresponding
        hex value in buttonColors. 
        """
        for button in self.button_list.Children:
            key = button.Content
            if key:
                try:
                    brush = BrushConverter().ConvertFrom(self.buttonColors[key])
                    button.Background = brush
                except:
                    pass

    @classmethod
    def show(cls, 
            buttonColors,  #pylint: disable=W0221
            context,
            xamlFilesDir,
            xamlSource,
            title='User Input',
            width=forms.DEFAULT_INPUTWINDOW_WIDTH,
            height=forms.DEFAULT_INPUTWINDOW_HEIGHT,
            **kwargs):
        """
        Show user input window.

        Args:
            context (any): window context element(s)
            title (str): window title
            **kwargs (any): other arguments to be passed to window
        """
        context = sorted(buttonColors.keys())
        dlg = cls(context,
                xamlFilesDir,
                xamlSource,
                title,
                width,
                height,
                **kwargs)
        dlg.buttonColors = buttonColors
        dlg.context = context
        dlg.colorButtons()
        dlg.ShowDialog()

        return dlg.response


class CompareParameterWindow(ColorSwitchWindow):

    def __init__(self,
                context,
                xamlFilesDir,
                xamlSource,
                title,
                width,
                height,
                **kwargs):
        super(CompareParameterWindow, self).__init__(context,
                                                xamlFilesDir,
                                                xamlSource,
                                                title,
                                                width,
                                                height,
                                                **kwargs)

    @classmethod
    def show(cls, 
            buttonColors,  #pylint: disable=W0221
            paramValuesDict,
            xamlFilesDir,
            xamlSource,
            title='User Input',
            width=forms.DEFAULT_INPUTWINDOW_WIDTH,
            height=forms.DEFAULT_INPUTWINDOW_HEIGHT,
            **kwargs):
        """
        Show user input window.

        Args:
            context (any): window context element(s)
            title (str): window title
            width (int): window width
            height (int): window height
            **kwargs (any): other arguments to be passed to window
        """
        context = sorted(buttonColors.keys())
        dlg = cls(context,
                xamlFilesDir,
                xamlSource,
                title,
                width,
                height,
                **kwargs)
        dlg.buttonColors = buttonColors
        dlg.paramValuesDict = paramValuesDict
        dlg.colorButtons()
        dlg.Show()

    def process_option(self, sender, args):    #pylint: disable=W0613
        """Handle click on command option button."""
        self.Close()
        if sender:
            selectionIds = [revitron.DB.ElementId(int(x)) for x in self.paramValuesDict['values'][sender.Content]]
            revitron.Selection.set(selectionIds)


class AreaHelperWindow(Windows.Window):
    def __init__(self,xamlfile,areaHelperManager):
        """
        Shows Area Helper window.
        As a non-modal window, 
        transactions are in event manager integrated,
        which triggers external commands.

        Args:
            xamlfile (str): xaml file path
            areaHelperManager (obj): Area Helper Manager instance
        """
        wpf.LoadComponent(self, xamlfile)
        self.areaHelperManager = areaHelperManager
        self.refresh_event = EventManager()
        self.bake_event = EventManager()
        self.close_event = EventManager()
        self.areaHelperCheck = False
        self.updateStatus()
        self.refreshUi()
        self.combo_scheme.ItemsSource = self.areaHelperManager.AreaDict

        self.refresh_event.setFunctions(self.areaHelperManager.toggle,
                                        self.updateStatus,
                                        self.refreshUi)
        self.bake_event.setFunctions(self.areaHelperManager.bakeDishapes,
                                        self.updateStatus,
                                        self.refreshUi)                                
        self.close_event.setFunctions(self.areaHelperManager.removeDishapes)
    
    def updateSelectedAreas(self):
        """
        fetch selected areas according to combo box
        """
        self.areaHelperManager.updateAreas(self.combo_scheme.SelectedValue,
                                            self.combo_level.SelectedValue)
    
    def comboSchemeChanged(self,sender,args):
        """
        on scheme combobox changed,
        updates level combobox and refreshed buttons
        """
        level_list = self.areaHelperManager.AreaDict[
                        self.combo_scheme.SelectedValue]
        level_list = self.changeOrder(level_list.keys())
        self.combo_level.ItemsSource = level_list
        self.updateSelectedAreas()
        self.refreshUi()
        self.combo_level.SelectedValue = "- ALL -"

    def comboLevelChanged(self,sender,args):
        """on level combobox changed,
        updates area list from that level"""
        self.updateSelectedAreas()
        self.refreshUi()

    def updateStatus(self):
        """calls check status function from area helper manager"""
        self.areaHelperCheck = self.areaHelperManager.checkStatus()

    def refreshUi(self):
        """
        updates ui according to area helper check result
        """
        if self.areaHelperCheck:
            self.button_refresh.Content = "Purge"
            self.button_bake.Content = "Bake"
            self.button_refresh.Tag = ""
            refreshEnable = True
            bakeEnable = True
            comboEnable = False
        elif self.areaHelperManager.Areas:
            self.button_refresh.Content = "Visualize"
            self.button_bake.Content = ""
            self.button_refresh.Tag = len(self.areaHelperManager.Areas)
            refreshEnable = True
            bakeEnable = False
            comboEnable = True
        else:
            self.button_refresh.Content = ""
            self.button_bake.Content = ""
            self.button_refresh.Tag = ""
            refreshEnable = False
            bakeEnable = False
            comboEnable = True

        self.button_refresh.IsEnabled = refreshEnable
        self.button_bake.IsEnabled - bakeEnable
        self.combo_scheme.IsEnabled = comboEnable
        self.combo_level.IsEnabled = comboEnable

    def changeOrder(self,list):
        """
        sorts level list,
        adds '- ALL -' to top
        """
        if list:
            x = "- ALL -"
            if x in list:
                list.remove(x)
                list.sort()
                list.insert(0,x)
            return list
        else:
            return []

    def refreshClicked(self,sender,e):
        """
        on visualize/purge clicked,
        raises refresh event
        """
        try:
            self.areaHelperManager.updateAreaDict()
            self.updateSelectedAreas()
            self.refresh_event.raiseEvent() 
        except:
            import traceback
            print traceback.format_exc()
    
    def bakeClicked(self,sender,e):
        """
        on bake clicked,
        raises bake event
        """
        try:
            self.areaHelperManager.updateAreaDict()
            self.updateSelectedAreas()
            self.bake_event.raiseEvent() 
        except:
            import traceback
            print traceback.format_exc()
  
    def windowClosing(self,sender,e):
        """
        on windowing closing,
        raises event to purge not baked
        """
        try:

            self.close_event.raiseEvent()
        except:
            import traceback
            print traceback.format_exc()



