def get_screen_size():
    # get pixle size of the screen
    # return [width, height]
    from win32.lib import win32con
    from win32 import win32gui, win32print
    hDC = win32gui.GetDC(0)
    width_f = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
    height_f = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
    return [width_f, height_f]


def font_get(para_dict_f={"Family":None,
                        'PointSize':None,
                        'PixelSize':None,
                        'Bold':None,
                        'Italic':None,
                        'Weight':None,
                        'Underline':None,
                        'LetterSpacing':None,
                        'WordSpacing':None,
                        'Stretch':None,
                        'StrikeOut':None}):
    # produce font with family and size
    from PySide2.QtGui import QFont
    font_f = QFont()
    font_f.setStyleStrategy(QFont.PreferAntialias)
    allowed_keys = ["Family", "PointSize", "Bold", "Italic", "Weight", "Underline", "StrikeOut", 
                    "LetterSpacing", "WordSpacing", "Stretch", 'PixelSize']
    for key, value in para_dict_f.items():
        if (key in allowed_keys) and value:
            dict_f = {'font_f':font_f,
                      'value':value}
            exec(f'font_f.set{key}(value)', dict_f)
    return font_f