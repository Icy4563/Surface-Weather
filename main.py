import requests
from datetime import datetime
import kivy
import kivymd
from kivy.clock import Clock
import time
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.text import LabelBase
from kivy.metrics import sp, dp
from datetime import date
import calendar
from kivy.storage.jsonstore import JsonStore
from kivy.core.window import Window
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
import citysearch
import surface_w_utilities
from kivy.uix.floatlayout import FloatLayout


cacheWeather = None
cacheCurrentWeather = None

storage = JsonStore("userOptions.json")

continueUIBuild = True

class RootElement(FloatLayout):
    pass

#pretty obvious, requests the weather from the MET Norway API
def requestWeather(email, lat, lon):
    thing = surface_w_utilities.requestWeather(email, lat, lon)
    return thing

#===========chatGPT generated parsers for the weather API response JSON===========
def parse_met_time(iso_str):
    thing = surface_w_utilities.parse_met_time(iso_str)

    return thing

def extract_weather_tuple(entry):
    thing = surface_w_utilities.extract_weather_tuple(entry)

    return thing

def getCurrentWeather(json_data, now=None):
    thing = surface_w_utilities.getCurrentWeather(json_data, now)

    return thing

def getForecastPrecise(json_data, day_offset, hour, include_date=False):
    thing = surface_w_utilities.getForecastPrecise(json_data, day_offset, hour, include_date)
    return thing


#===========================================================================

#IP API to get relative location without GPS hassle (+ time zone)
def getIPstuff():
    global UTCoffset
    thing = surface_w_utilities.getIPstuff()
    UTCoffset = thing[3]

    return thing

def shortenMonth(MonthIO):
    thing = surface_w_utilities.shortenMonth(MonthIO)
    return thing

def getWeekday(source=date.weekday(date.today()), shorten=False):
    thing =  surface_w_utilities.getWeekday(source, shorten)

    return thing

#ToDo: make region selection automatic
def hemisphereTimeOps(inputHour, Western=True):
    global UTCoffset
    thing = surface_w_utilities.hemisphereTimeOps(inputHour, Western, UTCoffset)
    return thing

#if statements to deduce rain (precipitation) probability from quantity
def getRainProbability(source):
    thing =  surface_w_utilities.getRainProbability(source)

    return thing

#if statements to find the appropriate weather icon, with the current parameter to select whether to find the icon for current weather
#or for forecasting
def getWeatherIcon(source):
    global vocabIcon
    thing = surface_w_utilities.getWeatherIcon(source)
    icon = thing[0]
    vocabIcon = thing[1]

    return icon

#Custom font imports, and main build function for general logic and UI Setup
class SurfaceWeatherApp(MDApp):
    def build(self):
        self.weatherFetchedAlready = False
        self.westerSelected = False
        self.hemisphereSelectedAlready = False
        self.savedEmail = None
        self.toggledFlag = True

        self.lancity1 = None
        self.loncity1= None
        self.lancity2 = None
        self.loncity2= None
        self.lancity3 = None
        self.loncity3= None
        self.lancity4 = None
        self.loncity4= None
        self.lancity5 = None
        self.loncity5= None
        self.lancity6 = None
        self.loncity6= None
        self.lancity7 = None
        self.loncity7= None
        self.lancity8 = None
        self.loncity8= None

        self.dateStuff = None

        Window.bind(on_resize=self.safelyCallScaling)
        Window.bind(on_keyboard_height=self.keyboardTextInput)

        LabelBase.register(name="urbanist", fn_regular="Urbanist-Regular.ttf")

        self.theme_cls.font_styles["urbanist"] = {
            "large": {
                "line-height": 1.26,
                "font-name": "urbanist",
                "font-size": sp(57),
            },
            "medium": {
                "line-height": 1.42,
                "font-name": "urbanist",
                "font-size": sp(45),
            },
            "small": {
                "line-height": .9,
                "font-name": "urbanist",
                "font-size": sp(32),
        }
        }

        LabelBase.register(name="urbanistSMALL", fn_regular="Urbanist-Regular.ttf")

        self.theme_cls.font_styles["urbanistSMALL"] = {
            "large": {
                "line-height": 1.26,
                "font-name": "urbanistSMALL",
                "font-size": sp(37),
            },
            "medium": {
                "line-height": .9,
                "font-name": "urbanistSMALL",
                "font-size": sp(27),
            },
            "small": {
                "line-height": 1.35,
                "font-name": "urbanistSMALL",
                "font-size": sp(13),
        }
        }

        LabelBase.register(name="urbanistSMALL2", fn_regular="Urbanist-Regular.ttf")

        self.theme_cls.font_styles["urbanistSMALL2"] = {
            "large": {
                "line-height": 1.26,
                "font-name": "urbanistSMALL2",
                "font-size": sp(22),
            },
            "medium": {
                "line-height": 1.42,
                "font-name": "urbanistSMALL2",
                "font-size": sp(15),
            },
            "small": {
                "line-height": 1.35,
                "font-name": "urbanistSMALL2",
                "font-size": sp(2),
        }
        }

        self.theme_cls.dynamic_scheme_name = "VIBRANT"
        self.theme_cls.theme_style_switch_animation = True
        if storage.exists("color"):
            self.theme_cls.primary_palette = storage.get("color")["color"]
        else:
            self.theme_cls.primary_palette = "Darkgrey"
        if storage.exists("theme"):
            self.theme_cls.theme_style = storage.get("theme")["theme"]
        else:
            self.theme_cls.theme_style = "Light"

        return Builder.load_file("main.kv")
    
    def navBarHandler(
        self,
        bar: MDNavigationBar,
        item: MDNavigationItem,
        item_icon: str,
        item_text: str,
    ):
        if item_text == "Current":
            call = "currentWeather"
            MDApp.get_running_app().root.ids.sm.transition.direction = 'right'
            MDApp.get_running_app().root.ids.sm.transition.speed = 3
        elif item_text == "Daily":
            call = "forecastWeatherScreen"
            MDApp.get_running_app().root.ids.sm.transition.direction = 'left'
            MDApp.get_running_app().root.ids.sm.transition.speed = 3

        MDApp.get_running_app().root.ids.sm.current = call

    def safelyCallScaling(self, *args):
        Clock.schedule_once(self.dynamicWindowScale, 0)

    def onHemisphereSelected(self, item, is_active):
        if not storage.exists('hemisphere'):
            if not is_active:
                return
            
            self.westerSelected = (item.value == "western")
            self.callAPI(self.savedEmail)
            MDApp.get_running_app().root.ids.sm.current = "currentWeather"

            storage.put('hemisphere', hemisphere=self.westerSelected)

            return self.westerSelected
        
        elif storage.exists("hemisphere")['hemisphere']:
            self.westerSelected = storage.get('hemisphere')
            self.callAPI(self.savedEmail)
            MDApp.get_running_app().root.ids.sm.current = "currentWeather"
            return self.westerSelected

    def callAPI(self, email):
        global currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount, cacheWeather, cacheCurrentWeather, continueUIBuild, year, month, day, hour, minute, second, weekday, dayy, DST, UTCoffset
        global continueUIBuild, city, lat1, lon1

        try:
            cacheIP = getIPstuff()

            if cacheIP:
                city, lat1, lon1, UTCoffset = cacheIP
            else:
                cacheIP = (0, 0, 0, 0)
                city, lat1, lon1, UTCoffset = cacheIP
                
            cacheWeather = requestWeather(email, lat1, lon1)
            cacheCurrentWeather = getCurrentWeather(cacheWeather)
            if cacheWeather:
                currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount = cacheCurrentWeather
                currentWindSpeed = currentWindSpeed * 3.6
            else:
                cacheWeather = (0, 0, 0, 0, 0)
                currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount = cacheCurrentWeather
        except Exception as e:
            continueUIBuild = False
            print(e, "errorrrrr")

        self.UILogic()
        self.dynamicWindowScale(1, Window.width, Window.height)

    def citySelectedHandler(self, ref_city_value, *args):
        global city, lat1, lon1, cacheWeather, cacheCurrentWeather
        global currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount, vocabIcon

        try:

            email = storage.get("email")["email"]

            research = citysearch.get_coordinates(ref_city_value)

            if isinstance(research, list):
                research = research[0]
            else:
                research = research

            city = research[0]
            lat1 = research[3]
            lon1 = research[4]

            cacheWeather = requestWeather(email, lat1, lon1)
            cacheCurrentWeather = getCurrentWeather(cacheWeather)

            currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount = cacheCurrentWeather
            currentWindSpeed *= 3.6

            # Update vocabIcon so "and {vocabIcon}" refreshes
            getWeatherIcon(cacheCurrentWeather)

            self.RealUILogic()
            MDApp.get_running_app().root.ids.sm.current = "currentWeather"

        except:
            pass


    def optionsSaved(self, email):
        if not storage.exists('email'):
            if self.savedEmail:
                return
            
            self.savedEmail = email

            storage.put('email', email=self.savedEmail)

            MDApp.get_running_app().root.ids.sm.current = "hemisphereSelect"

        if storage.exists('email'):
            self.savedEmail = storage.get('email')['email']
            MDApp.get_running_app().root.ids.sm.current = "hemisphereSelect"

    def searchCities(self, cityName):
        results = citysearch.get_coordinates(cityName, partial=True)
        screen = MDApp.get_running_app().root.ids.sm.get_screen('CitySelectScreen')

        if len(results) == 1:
            result1 = results[0]
            screen.ids.cityone.text = f"[ref={result1[0]}]{result1[0]}[/ref]"
            screen.ids.cityonedesc.text = f"{result1[1]}"

        elif len(results) == 2:
            result1, result2 = results[0], results[1]
            screen.ids.cityone.text = f"[ref={result1[0]}]{result1[0]}[/ref]"
            screen.ids.cityonedesc.text = f"{result1[1]}"
            screen.ids.citytwo.text = f"[ref={result2[0]}]{result2[0]}[/ref]"
            screen.ids.citytwodesc.text = f"{result2[1]}"

        elif len(results) == 3:
            result1, result2, result3 = results[0], results[1], results[2]
            screen.ids.cityone.text = f"[ref={result1[0]}]{result1[0]}[/ref]"
            screen.ids.cityonedesc.text = f"{result1[1]}"
            screen.ids.citytwo.text = f"[ref={result2[0]}]{result2[0]}[/ref]"
            screen.ids.citytwodesc.text = f"{result2[1]}"
            screen.ids.citythree.text = f"[ref={result3[0]}]{result3[0]}[/ref]"
            screen.ids.citythreedesc.text = f"{result3[1]}"

        elif len(results) == 4:
            result1, result2, result3, result4 = results[:4]
            screen.ids.cityone.text = f"[ref={result1[0]}]{result1[0]}[/ref]"
            screen.ids.cityonedesc.text = f"{result1[1]}"
            screen.ids.citytwo.text = f"[ref={result2[0]}]{result2[0]}[/ref]"
            screen.ids.citytwodesc.text = f"{result2[1]}"
            screen.ids.citythree.text = f"[ref={result3[0]}]{result3[0]}[/ref]"
            screen.ids.citythreedesc.text = f"{result3[1]}"
            screen.ids.cityfour.text = f"[ref={result4[0]}]{result4[0]}[/ref]"
            screen.ids.cityfourdesc.text = f"{result4[1]}"

        elif len(results) == 5:
            result1, result2, result3, result4, result5 = results[:5]
            screen.ids.cityone.text = f"[ref={result1[0]}]{result1[0]}[/ref]"
            screen.ids.cityonedesc.text = f"{result1[1]}"
            screen.ids.citytwo.text = f"[ref={result2[0]}]{result2[0]}[/ref]"
            screen.ids.citytwodesc.text = f"{result2[1]}"
            screen.ids.citythree.text = f"[ref={result3[0]}]{result3[0]}[/ref]"
            screen.ids.citythreedesc.text = f"{result3[1]}"
            screen.ids.cityfour.text = f"[ref={result4[0]}]{result4[0]}[/ref]"
            screen.ids.cityfourdesc.text = f"{result4[1]}"
            screen.ids.cityfive.text = f"[ref={result5[0]}]{result5[0]}[/ref]"
            screen.ids.cityfivedesc.text = f"{result5[1]}"

        elif len(results) == 6:
            result1, result2, result3, result4, result5, result6 = results[:6]
            screen.ids.cityone.text = f"[ref={result1[0]}]{result1[0]}[/ref]"
            screen.ids.cityonedesc.text = f"{result1[1]}"
            screen.ids.citytwo.text = f"[ref={result2[0]}]{result2[0]}[/ref]"
            screen.ids.citytwodesc.text = f"{result2[1]}"
            screen.ids.citythree.text = f"[ref={result3[0]}]{result3[0]}[/ref]"
            screen.ids.citythreedesc.text = f"{result3[1]}"
            screen.ids.cityfour.text = f"[ref={result4[0]}]{result4[0]}[/ref]"
            screen.ids.cityfourdesc.text = f"{result4[1]}"
            screen.ids.cityfive.text = f"[ref={result5[0]}]{result5[0]}[/ref]"
            screen.ids.cityfivedesc.text = f"{result5[1]}"
            screen.ids.citysix.text = f"[ref={result6[0]}]{result6[0]}[/ref]"
            screen.ids.citysixdesc.text = f"{result6[1]}"

        elif len(results) == 7:
            result1, result2, result3, result4, result5, result6, result7 = results[:7]
            screen.ids.cityone.text = f"[ref={result1[0]}]{result1[0]}[/ref]"
            screen.ids.cityonedesc.text = f"{result1[1]}"
            screen.ids.citytwo.text = f"[ref={result2[0]}]{result2[0]}[/ref]"
            screen.ids.citytwodesc.text = f"{result2[1]}"
            screen.ids.citythree.text = f"[ref={result3[0]}]{result3[0]}[/ref]"
            screen.ids.citythreedesc.text = f"{result3[1]}"
            screen.ids.cityfour.text = f"[ref={result4[0]}]{result4[0]}[/ref]"
            screen.ids.cityfourdesc.text = f"{result4[1]}"
            screen.ids.cityfive.text = f"[ref={result5[0]}]{result5[0]}[/ref]"
            screen.ids.cityfivedesc.text = f"{result5[1]}"
            screen.ids.citysix.text = f"[ref={result6[0]}]{result6[0]}[/ref]"
            screen.ids.citysixdesc.text = f"{result6[1]}"
            screen.ids.cityseven.text = f"[ref={result7[0]}]{result7[0]}[/ref]"
            screen.ids.citysevendesc.text = f"{result7[1]}"

        elif len(results) >= 8:
            result1, result2, result3, result4, result5, result6, result7, result8 = results[:8]
            screen.ids.cityone.text = f"[ref={result1[0]}]{result1[0]}[/ref]"
            screen.ids.cityonedesc.text = f"{result1[1]}"
            screen.ids.citytwo.text = f"[ref={result2[0]}]{result2[0]}[/ref]"
            screen.ids.citytwodesc.text = f"{result2[1]}"
            screen.ids.citythree.text = f"[ref={result3[0]}]{result3[0]}[/ref]"
            screen.ids.citythreedesc.text = f"{result3[1]}"
            screen.ids.cityfour.text = f"[ref={result4[0]}]{result4[0]}[/ref]"
            screen.ids.cityfourdesc.text = f"{result4[1]}"
            screen.ids.cityfive.text = f"[ref={result5[0]}]{result5[0]}[/ref]"
            screen.ids.cityfivedesc.text = f"{result5[1]}"
            screen.ids.citysix.text = f"[ref={result6[0]}]{result6[0]}[/ref]"
            screen.ids.citysixdesc.text = f"{result6[1]}"
            screen.ids.cityseven.text = f"[ref={result7[0]}]{result7[0]}[/ref]"
            screen.ids.citysevendesc.text = f"{result7[1]}"
            screen.ids.cityeight.text = f"[ref={result8[0]}]{result8[0]}[/ref]"
            screen.ids.cityeightdesc.text = f"{result8[1]}"
                
        elif len(results) <= 0:
            return

    def citychanger(self, instance, ref):
        MDApp.get_running_app().root.ids.sm.current = "CitySelectScreen"

    def keyboardTextInput(self, window, height, *args):
        if not height == 0:
            MDApp.get_running_app().root.ids.sm.get_screen('emailInput').ids.email_input.pos_hint = {'center_x': 0.5,'center_y': 0.85}
        else:
            MDApp.get_running_app().root.ids.sm.get_screen('emailInput').ids.email_input.pos_hint = {'center_x': 0.5,'center_y': 0.5}

    def dynamicWindowScale(self, *args):
        width, height = Window.size

        if width <= dp(775):
            #scaling of main weather current card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.currentWeatherCard.size_hint = .9621, .25
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.currentWeatherCard.pos_hint = {'center_x': .506,'center_y': .835}

            #scaling of humidity card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humidityCard.pos_hint = {'center_x': 0.1853,'center_y': 0.635}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humidityCard.size_hint = .325, .127
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humidityText.font_style = "urbanistSMALL"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humidityText.role = "medium"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humIcon.pos_hint = {"center_x": .1665, "center_y": .81}

            #scaling of the cloud cover card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudCard.pos_hint = {'center_x': 0.528,'center_y': 0.635}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudCard.size_hint = .325, .127
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudIcon.pos_hint = {'center_x': .1695,'center_y': .8115}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudCoverText.font_style = "urbanistSMALL"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudCoverText.role = "medium"

            #scaling of the forecast card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.forecastCard.pos_hint = {'center_x': 0.506,'center_y': 0.46}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.forecastCard.size_hint = .9621, .195

            #scaling of the wind speed card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windCard.pos_hint = {'center_x': 0.847,'center_y': 0.635}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windCard.size_hint = .275, .127
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windIcon.theme_font_size = "Custom"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windIcon.font_size = sp(19)
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windIcon.pos_hint = {'center_x': .15,'center_y': 0.845}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windSpeedText.font_style = "urbanistSMALL"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windSpeedText.role = "medium"

            #scaling of the current rain amount card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.rainCard.pos_hint = {'center_x': 0.255,'center_y': 0.275}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.rainCard.size_hint = .455, .15
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.rainIconStatic.pos_hint = {'center_x': 0.1,'center_y': 0.82}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.rainAmountText.role = "small"

            #scaling of the time card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.timeCard.pos_hint = {'center_x': 0.746,'center_y': 0.275}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.timeCard.size_hint = .4875, .15

            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.timeText.pos_hint = {'center_x': .5,'center_y': .685}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.dateText.pos_hint = {'center_x': .5,'center_y': .2065}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.dateText.font_style = "urbanistSMALL2"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.dateText.role = "large"


            #forecast scaling
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tmrTextStatic.text = "tmr"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tmrTextStatic.pos_hint = {'center_x': .13,'center_y': .7}

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayOne.font_style = "urbanistSMALL2"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayOne.role = "large"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayOne.pos_hint = {'center_x': .1265,'center_y': .7}

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayTwo.font_style = "urbanistSMALL2"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayTwo.role = "large"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayTwo.pos_hint = {'center_x': .1265,'center_y': .7}

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayThree.font_style = "urbanistSMALL2"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayThree.role = "large"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayThree.pos_hint = {'center_x': .1265,'center_y': .7}

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayFour.font_style = "urbanistSMALL2"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayFour.role = "large"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayFour.pos_hint = {'center_x': .1265,'center_y': .7}

            #extra stuff dw about it
            if self.dateStuff:
                MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.dateText.text = str(f"{getWeekday(shorten=True)}, {self.dateStuff.day} of {shortenMonth(self.month_name)}")
            else:
                pass
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticHumText.text = ""
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticCloudText.text = ""
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticWindText.text = ""
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticRainText.text = ""

        elif not width <= dp(775):
            #reverse scaling of things not to worry about
            if self.dateStuff:
                MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.dateText.text = str(f"{getWeekday()}, {self.dateStuff.day} of {self.month_name}")
            else:
                pass
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticHumText.text = "humidity"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticWindText.text = "wind speed"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticCloudText.text = "cloud cover"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticRainText.text = "rain quantity"

            #reverse scaling of main weather current card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.currentWeatherCard.size_hint = .45, .3
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.currentWeatherCard.pos_hint = {'center_x': .25,'center_y': .825}

            #reverse scaling of humidity card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humidityCard.pos_hint = {'center_x': .645,'center_y': .902}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humidityCard.size_hint = .3, .135
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticHumText.pos_hint = {'center_x': .235,'center_y': .79}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humidityText.font_style = "urbanist"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humidityText.role = "small"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humIcon.pos_hint = {"center_x": .1, "center_y": .785}

            #reverse scaling of the cloud cover card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudCard.pos_hint = {'center_x': 0.645,'center_y': 0.745}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudCard.size_hint = .3, .135
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticCloudText.pos_hint = {'center_x': .2885,'center_y': .79}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudCoverText.font_style = "urbanist"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudCoverText.role = "small"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudIcon.pos_hint = {"center_x": .1, "center_y": .785}

            #reverse scaling of the forecast card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.forecastCard.pos_hint = {'center_x': 0.506,'center_y': 0.525}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.forecastCard.size_hint = .9621, .25

            #reverse scaling of the wind speed card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windCard.pos_hint = {'center_x': .9,'center_y': 0.825}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windCard.size_hint = .17575, .291
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windIcon.theme_font_size = "Custom"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windIcon.font_size = sp(24)
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windIcon.pos_hint = {'center_x': .125,'center_y': 0.885}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.staticWindText.pos_hint = {'center_x': .45,'center_y': 0.885}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windSpeedText.font_style = "urbanist"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windSpeedText.role = "small"

            #reverse scaling of the current rain amount card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.rainCard.pos_hint = {'center_x': 0.26,'center_y': 0.305}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.rainCard.size_hint = .47, .15
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.rainIconStatic.pos_hint = {'center_x': 0.0685,'center_y': 0.82}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.rainAmountText.role = "medium"

            #reverse scaling of the time card
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.timeCard.pos_hint = {'center_x': 0.7525,'center_y': 0.305}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.timeCard.size_hint = .4875, .15

            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.timeText.pos_hint = {'center_x': .1655,'center_y': .5}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.dateText.pos_hint = {'center_x': .645,'center_y': .415}
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.dateText.font_style = "urbanistSMALL"
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.dateText.role = "medium"

            #reverse forecast scaling
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tmrTextStatic.text = "tomorrow"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tmrTextStatic.pos_hint = {'center_x': .12,'center_y': .7}

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayOne.font_style = "urbanistSMALL"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayOne.role = "medium"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayOne.pos_hint = {'center_x': .12,'center_y': .7}

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayTwo.font_style = "urbanistSMALL"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayTwo.role = "medium"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayTwo.pos_hint = {'center_x': .12,'center_y': .7}

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayThree.font_style = "urbanistSMALL"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayThree.role = "medium"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayThree.pos_hint = {'center_x': .12,'center_y': .7}

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayFour.font_style = "urbanistSMALL"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayFour.role = "medium"
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayFour.pos_hint = {'center_x': .12,'center_y': .7}


    def darkThemeHandler(self):
        self.theme_cls.theme_style = "Dark"

        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greyCirc.icon_color = 0.4431372549, 0.4431372549, 0.4352941176, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.redCirc.icon_color = 0.8196078431, 0.2745098039, 0.1725490196, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.blueCirc.icon_color = 0.4647887324, 0.7215686275, 0.8156862745, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greenCirc.icon_color = 0.6313725490, 0.6470588235, 0.3372549020, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.purpleCirc.icon_color = 0.4, 0.3058823529, 0.5333333333, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.darkCirc.icon_color = .1725490196, 0.1764705882, 0.1764705882, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.lightCirc.icon_color = 0.9764705882, 0.9764705882, 0.9764705882, 0.9

        storage.put("theme", theme="Dark")

    def lightThemeHandler(self):
        self.theme_cls.theme_style = "Light"

        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greyCirc.icon_color = 0.4431372549, 0.4431372549, 0.4352941176, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.redCirc.icon_color = 0.8196078431, 0.2745098039, 0.1725490196, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.blueCirc.icon_color = 0.4647887324, 0.7215686275, 0.8156862745, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greenCirc.icon_color = 0.6313725490, 0.6470588235, 0.3372549020, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.purpleCirc.icon_color = 0.4, 0.3058823529, 0.5333333333, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.darkCirc.icon_color = .1725490196, 0.1764705882, 0.1764705882, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.lightCirc.icon_color = 0.9764705882, 0.9764705882, 0.9764705882, 0.9

        storage.put("theme", theme="Light")

    def dropdownHandler(self):
        self.menu.open()

    def themeHandler(self, *args):
        MDApp.get_running_app().root.ids.sm.transition.direction = "up"
        MDApp.get_running_app().root.ids.sm.current = "themeSelect"
        self.menu.dismiss()

    def backButtonHandler(self):
        MDApp.get_running_app().root.ids.sm.transition.direction = "down"
        MDApp.get_running_app().root.ids.sm.current = "forecastWeatherScreen"

    def greySchemeHandler(self):
        self.theme_cls.primary_palette = "Dimgray"

        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greyCirc.icon_color = 0.4431372549, 0.4431372549, 0.4352941176, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.redCirc.icon_color = 0.8196078431, 0.2745098039, 0.1725490196, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.blueCirc.icon_color = 0.4647887324, 0.7215686275, 0.8156862745, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greenCirc.icon_color = 0.6313725490, 0.6470588235, 0.3372549020, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.purpleCirc.icon_color = 0.4, 0.3058823529, 0.5333333333, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.darkCirc.icon_color = .1725490196, 0.1764705882, 0.1764705882, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.lightCirc.icon_color = 0.9764705882, 0.9764705882, 0.9764705882, 0.9

        storage.put("color", color="dimgray")

    def redSchemeHandler(self):
        self.theme_cls.primary_palette = "Coral"

        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greyCirc.icon_color = 0.4431372549, 0.4431372549, 0.4352941176, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.redCirc.icon_color = 0.8196078431, 0.2745098039, 0.1725490196, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.blueCirc.icon_color = 0.4647887324, 0.7215686275, 0.8156862745, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greenCirc.icon_color = 0.6313725490, 0.6470588235, 0.3372549020, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.purpleCirc.icon_color = 0.4, 0.3058823529, 0.5333333333, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.darkCirc.icon_color = .1725490196, 0.1764705882, 0.1764705882, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.lightCirc.icon_color = 0.9764705882, 0.9764705882, 0.9764705882, 0.9

        storage.put("color", color="Coral")

    def blueSchemeHandler(self):
        self.theme_cls.primary_palette = "Cyan"

        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greyCirc.icon_color = 0.4431372549, 0.4431372549, 0.4352941176, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.redCirc.icon_color = 0.8196078431, 0.2745098039, 0.1725490196, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.blueCirc.icon_color = 0.4647887324, 0.7215686275, 0.8156862745, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greenCirc.icon_color = 0.6313725490, 0.6470588235, 0.3372549020, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.purpleCirc.icon_color = 0.4, 0.3058823529, 0.5333333333, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.darkCirc.icon_color = .1725490196, 0.1764705882, 0.1764705882, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.lightCirc.icon_color = 0.9764705882, 0.9764705882, 0.9764705882, 0.9

        storage.put("color", color="Cyan")

    def greenSchemeHandler(self):
        self.theme_cls.primary_palette = "Darkkhaki"

        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greyCirc.icon_color = 0.4431372549, 0.4431372549, 0.4352941176, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.redCirc.icon_color = 0.8196078431, 0.2745098039, 0.1725490196, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.blueCirc.icon_color = 0.4647887324, 0.7215686275, 0.8156862745, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greenCirc.icon_color = 0.6313725490, 0.6470588235, 0.3372549020, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.purpleCirc.icon_color = 0.4, 0.3058823529, 0.5333333333, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.darkCirc.icon_color = .1725490196, 0.1764705882, 0.1764705882, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.lightCirc.icon_color = 0.9764705882, 0.9764705882, 0.9764705882, 0.9

        storage.put("color", color="Darkkhaki")

    def purpleSchemeHandler(self):
        self.theme_cls.primary_palette = "Fuchsia"

        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greyCirc.icon_color = 0.4431372549, 0.4431372549, 0.4352941176, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.redCirc.icon_color = 0.8196078431, 0.2745098039, 0.1725490196, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.blueCirc.icon_color = 0.4647887324, 0.7215686275, 0.8156862745, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.greenCirc.icon_color = 0.6313725490, 0.6470588235, 0.3372549020, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("colorSelect").ids.purpleCirc.icon_color = 0.4, 0.3058823529, 0.5333333333, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.darkCirc.icon_color = .1725490196, 0.1764705882, 0.1764705882, 0.9
        MDApp.get_running_app().root.ids.sm.get_screen("themeSelect").ids.lightCirc.icon_color = 0.9764705882, 0.9764705882, 0.9764705882, 0.9

        storage.put("color", color="Fuchsia")

    def centerForecastScroll(self, *args):
        MDApp.get_running_app().root.ids.sm.get_screen("currentWeather").ids.todayScroll.scroll_x = 0.5

    def colorHandler(self, *args):
        MDApp.get_running_app().root.ids.sm.transition.direction = "up"
        MDApp.get_running_app().root.ids.sm.current = "colorSelect"
        self.menu.dismiss()

    def aboutHandler(self, *args):
        MDApp.get_running_app().root.ids.sm.transition.direction = "up"
        MDApp.get_running_app().root.ids.sm.current = "AboutScreen"
        self.menu.dismiss()

    def refreshTimeVariables(self, dt):
        global currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount, cacheWeather, cacheCurrentWeather, continueUIBuild, year, month, day, hour, minute, second, weekday, dayy, DST, UTCoffset

        year, month, day, hour, minute, second, weekday, dayy, DST = time.gmtime()
        hour = hour + UTCoffset

        MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.timeText.text = str(f"{hour:02d}:{minute:02d}")

    def on_start(self):
        self.menu_items = [
            {
                "text": "Theme",
                "on_release": self.themeHandler,
            },
            {
                "text": "Color Scheme",
                "on_release": self.colorHandler,
            },
            {
                "text": "About",
                "on_release": self.aboutHandler,
            },
        ]
        self.menu = MDDropdownMenu(
            caller=MDApp.get_running_app().root.ids.sm.get_screen("forecastWeatherScreen").ids.settButton,
            items=self.menu_items,
            width_mult=4
        )

        self.theme_cls.set_colors()
        Clock.schedule_once(self.centerForecastScroll, 0)


#===Microsoft Copilot implementation fix to ensure jsonstore skips user prompts if already answered===
        if storage.exists('email'):
            self.savedEmail = storage.get('email')['email']

            if storage.exists('hemisphere'):
                self.westerSelected = storage.get('hemisphere')['hemisphere']

                self.callAPI(self.savedEmail)
                MDApp.get_running_app().root.ids.sm.current = "currentWeather"
                return

            MDApp.get_running_app().root.ids.sm.current = "hemisphereSelect"
            return

        MDApp.get_running_app().root.ids.sm.current = "emailInput"
#====================================================================================================
    def RealUILogic(self):
        global currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount, cacheWeather, cacheCurrentWeather, continueUIBuild, year, month, day, hour, minute, second, weekday, dayy, DST, UTCoffset
        global continueUIBuild, city, lat1, lon1

        if continueUIBuild:
            dateStuff = datetime.now()
            self.dateStuff = dateStuff

            numberMonth = dateStuff.month
            month_name = calendar.month_name[numberMonth]
            self.month_name = month_name

            #add the live info / general UI logic
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cityText.text = str(f"in [ref=here]{city}[/ref], it is")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempText.text = str(f"{currentTemperature}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.currentWeatherIcon.icon = getWeatherIcon(cacheCurrentWeather) 
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.generalWeatherText.text = str(f"and {vocabIcon}")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.humidityText.text = str(f"{currentRelHumidity}%")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.cloudCoverText.text = str(f"{currentCloudArea}%")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.dateText.text = str(f"{getWeekday()}, {dateStuff.day} of {month_name}")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.rainAmountText.text = str(f"{currentPrecpAmount} mm")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerosixWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(6, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerosevenWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(7, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zeroeightWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(8, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zeronineWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(9, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerotenWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(10, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zeroelevenWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(11, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerotwelveWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(12, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerothirteenWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(13, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerofourteenWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(14, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerofifteenWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(15, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerosixteenWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(16, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zeroseventennWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(17, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zeroeightennWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(18, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zeroninteenWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(19, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerotwentyWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(20, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.zerotwentyoneWeatherIcon.icon = getWeatherIcon(getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(21, self.westerSelected)))
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextZero.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(1, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextTwo.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(2, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextThree.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(3, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextFour.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(4, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextFive.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(5, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextSeventeen.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(17, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextSix.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(6, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextSeven.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(7, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextEight.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(8, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextNine.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(9, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextTen.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(10, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextEleven.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(11, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextTwelve.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(12, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextThirteen.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(13, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextFourteen.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(14, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextFifteen.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(15, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextSixteen.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(16, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextEighteen.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(18, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextNinteen.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(19, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextTwenty.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(20, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextTwentyOne.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(21, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextTwentyTwo.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(22, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextTwentyThree.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(23, self.westerSelected))[0]}°")
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.tempTextTwentyFour.text = str(f"{getForecastPrecise(cacheWeather, 0, hemisphereTimeOps(24, self.westerSelected))[0]}°")

            #round wind speed to a more normal unit
            currentWindSpeed = round(currentWindSpeed)

            #and then display it (wind speed)
            MDApp.get_running_app().root.ids.sm.get_screen('currentWeather').ids.windSpeedText.text = str(f'''{currentWindSpeed}
km/h''')

            #display the time after convert, and update it every 5 seconds
            self.refreshTimeVariables(1)
            Clock.schedule_interval(self.refreshTimeVariables, 12)

            #now the forecast days
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayOne.text = str(f"{getForecastPrecise(cacheWeather, 1, hemisphereTimeOps(6, self.westerSelected), True)[5]}")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayTwo.text = str(f"{getForecastPrecise(cacheWeather, 2, hemisphereTimeOps(6, self.westerSelected), True)[5]}")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayThree.text = str(f"{getForecastPrecise(cacheWeather, 3, hemisphereTimeOps(6, self.westerSelected), True)[5]}")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.followingDayFour.text = str(f"{getForecastPrecise(cacheWeather, 4, hemisphereTimeOps(6, self.westerSelected), True)[5]}")

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tomorrowWeatherIconHSix.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 1, hemisphereTimeOps(6, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tomorrowWeatherIconHTwelve.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 1, hemisphereTimeOps(12, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tomorrowWeatherIconHEighteen.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 1, hemisphereTimeOps(18, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextTmrSix.text = str(f"{round(getForecastPrecise(cacheWeather, 1, hemisphereTimeOps(6, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextTmrTwelve.text = str(f"{round(getForecastPrecise(cacheWeather, 1, hemisphereTimeOps(12, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextTmrEighteen.text = str(f"{round(getForecastPrecise(cacheWeather, 1, hemisphereTimeOps(18, self.westerSelected))[0])}°")

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.aftermorrowWeatherIconHSix.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 2, hemisphereTimeOps(6, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.aftermorrowWeatherIconHTwelve.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 2, hemisphereTimeOps(12, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.aftermorrowWeatherIconHEighteen.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 2, hemisphereTimeOps(18, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftTmrSix.text = str(f"{round(getForecastPrecise(cacheWeather, 2, hemisphereTimeOps(6, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftTmrTwelve.text = str(f"{round(getForecastPrecise(cacheWeather, 2, hemisphereTimeOps(12, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftTmrEighteen.text = str(f"{round(getForecastPrecise(cacheWeather, 3, hemisphereTimeOps(18, self.westerSelected))[0])}°")

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.afterTwomorrowWeatherIconHSix.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 3, hemisphereTimeOps(6, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.afterTwomorrowWeatherIconHTwelve.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 3, hemisphereTimeOps(12, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.afterTwomorrowWeatherIconHEighteen.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 3, hemisphereTimeOps(18, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftTwoTmrSix.text = str(f"{round(getForecastPrecise(cacheWeather, 3, hemisphereTimeOps(6, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftTwoTmrTwelve.text = str(f"{round(getForecastPrecise(cacheWeather, 3, hemisphereTimeOps(12, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftTwoTmrEighteen.text = str(f"{round(getForecastPrecise(cacheWeather, 3, hemisphereTimeOps(18, self.westerSelected))[0])}°")
            

            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.afterThreemorrowWeatherIconHSix.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 4, hemisphereTimeOps(6, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.afterThreemorrowWeatherIconHTwelve.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 4, hemisphereTimeOps(12, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.afterThreemorrowWeatherIconHEighteen.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 4, hemisphereTimeOps(18, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftThreeTmrSix.text = str(f"{round(getForecastPrecise(cacheWeather, 4, hemisphereTimeOps(6, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftThreeTmrTwelve.text = str(f"{round(getForecastPrecise(cacheWeather, 4, hemisphereTimeOps(12, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftThreeTmrEighteen.text = str(f"{round(getForecastPrecise(cacheWeather, 4, hemisphereTimeOps(18, self.westerSelected))[0])}°")
            
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.afterFourmorrowWeatherIconHSix.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 5, hemisphereTimeOps(6, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.afterFourmorrowWeatherIconHTwelve.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 5, hemisphereTimeOps(12, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.afterFourmorrowWeatherIconHEighteen.icon = (getWeatherIcon(getForecastPrecise(cacheWeather, 5, hemisphereTimeOps(18, self.westerSelected))))
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftFourTmrSix.text = str(f"{round(getForecastPrecise(cacheWeather, 5, hemisphereTimeOps(6, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftFourTmrTwelve.text = str(f"{round(getForecastPrecise(cacheWeather, 5, hemisphereTimeOps(12, self.westerSelected))[0])}°")
            MDApp.get_running_app().root.ids.sm.get_screen('forecastWeatherScreen').ids.tempTextaftFourTmrEighteen.text = str(f"{round(getForecastPrecise(cacheWeather, 5, hemisphereTimeOps(18, self.westerSelected))[0])}°")

        else:
            Clock.schedule_once(self.showError)

    def showError(self, *args):
        print("its error time")
        MDApp.get_running_app().root.ids.sm.current = "errorScreen"

    def UILogic(self):
        global currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount, cacheWeather, cacheCurrentWeather, continueUIBuild, year, month, day, hour, minute, second, weekday, dayy, DST, UTCoffset
        global continueUIBuild, city, lat1, lon1
        
        self.RealUILogic()
        
SurfaceWeatherApp().run()
