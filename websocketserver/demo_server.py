__author__ = 'chris'

import tornado.ioloop
import tornado.websocket
import random
import json
import datetime
from threading import Timer


TORNADO_PORT = 8888
NUMBER_OF_TEST_APPS = 4
MAX_MESSAGES_TO_SEND = 2
DEFAULT_URL = "www.chriszacny.com"
WEBSOCKET_PATH = "appdata"
REFRESH_RATE = 1.0


class JsonKeyStrings(object):
    Data = "data"
    Message = "message"
    AlertTypeText = "alert_type"
    Category = "category"
    Url = "url"
    CurrentAppHealth = "current_app_health"



class AppHealth(object):
    Good = 0
    Warn = 1
    Bad = 2
    Critical = 3


class AlertType(object):
    Information = "Information"
    Warning = "Warning"
    Error = "Error"
    ErrorHigh = "ErrorHigh"
    Critical = "Critical"


class Category(object):
    System = "System"
    Business = "Business"


class DomainMessage(object):
    def __init__(self, app_id, app_message, alert_type, category=None, url=None):
        self.app_id = app_id
        self.app_message = app_message
        self.alert_type = alert_type
        self.category = category
        self.url = url


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class Singleton(type):
    def __init__(self, *args, **kwargs):
        self.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super().__call__(*args, **kwargs)
            return self.__instance
        else:
            return self.__instance


class CachedApplicationData(metaclass=Singleton):
    def __init__(self):
        self.data = {}
        for i in range(0, NUMBER_OF_TEST_APPS):
            self.data[i+1] = []

    def get_appropriate_current_app_health(self, app_id):
        current_app_health = AppHealth.Good
        for domain_message in self.data[app_id]:
            if domain_message.alert_type == AlertType.Critical:
                if current_app_health < AppHealth.Critical:
                    current_app_health = AppHealth.Critical
            elif domain_message.alert_type == AlertType.ErrorHigh or domain_message.alert_type == AlertType.Error:
                if current_app_health < AppHealth.Bad:
                    current_app_health = AppHealth.Bad
            elif domain_message.alert_type == AlertType.Warning:
                if current_app_health < AppHealth.Warn:
                    current_app_health = AppHealth.Warn
        return current_app_health

    def update(self, json_message_payload):
        for i in range(0, NUMBER_OF_TEST_APPS):
            app_id = i+1
            for message_item in json_message_payload[app_id][JsonKeyStrings.Data]:
                domain_message = DomainMessage(app_id, message_item[JsonKeyStrings.Message], message_item[JsonKeyStrings.AlertTypeText], category=message_item[JsonKeyStrings.Category], url=message_item[JsonKeyStrings.Url])
                self.data[app_id].insert(0, domain_message)
            current_app_health = self.get_appropriate_current_app_health(app_id)
            json_message_payload[app_id][JsonKeyStrings.CurrentAppHealth] = current_app_health


class MainHandler(tornado.websocket.WebSocketHandler):
    def get_random_alert_type(self, alert_types):
        alert_seed = random.randint(0, 200)
        if alert_seed is 200:
            alert_type = alert_types[4]
        elif alert_seed is 199:
            alert_type = alert_types[3]
        elif alert_seed is 198:
            alert_type = alert_types[2]
        elif alert_seed is 197 or alert_seed is 196:
            alert_type = alert_types[1]
        else:
            alert_type = alert_types[0]
        return alert_type

    def hydrate_payload_with_random_data(self, alert_types, categories, message_payload):
        for i in range(0, NUMBER_OF_TEST_APPS):
            number_of_messages_to_send = random.randint(0, MAX_MESSAGES_TO_SEND)
            for j in range(0, number_of_messages_to_send):
                alert_type = self.get_random_alert_type(alert_types)
                category = categories[random.randint(0, 1)]
                this_message = "{} {} This is test data...".format(datetime.datetime.now().strftime("%y%m%d %H:%M"),
                                                                   alert_type)
                message_payload[i + 1][JsonKeyStrings.Data].append(
                    {JsonKeyStrings.AlertTypeText: alert_type, JsonKeyStrings.Message: this_message, JsonKeyStrings.Url: DEFAULT_URL,
                     JsonKeyStrings.Category: category})

    def random_message_burst(self):
        """
        Generate 4 sets of messages. This is all just mock data for now.
        """

        alert_types = {0: AlertType.Information, 1: AlertType.Warning, 2: AlertType.Error, 3: AlertType.ErrorHigh, 4: AlertType.Critical}
        categories = {0: Category.System, 1: Category.Business}

        message_payload = {1: {JsonKeyStrings.CurrentAppHealth: None, JsonKeyStrings.Data: []}, 2: {JsonKeyStrings.CurrentAppHealth: None, JsonKeyStrings.Data: []}, 3: {JsonKeyStrings.CurrentAppHealth: None, JsonKeyStrings.Data: []}, 4: {JsonKeyStrings.CurrentAppHealth: None, JsonKeyStrings.Data: []}}
        self.hydrate_payload_with_random_data(alert_types, categories, message_payload)
        CachedApplicationData().update(message_payload) # This will also update app_health
        self.write_message(json.dumps(message_payload))

    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket opened")

        # Every one seconds, send a random burst of messages to the client
        self.rt = RepeatedTimer(REFRESH_RATE, self.random_message_burst)

    def on_close(self):
        print("WebSocket closed")
        self.rt.stop()


def main():
    """
    In a real application, I'd also have a standard tornado tornado.web.RequestHandler handler that would handle standard HTTP RESTful requests.
    It would use something like jinja templating to generate the HTML. Of course there would also be tests, in addition to a logical module
    layout.
    """
    application = tornado.web.Application([(r"/{}".format(WEBSOCKET_PATH), MainHandler)])
    port = TORNADO_PORT
    application.listen(port)
    print("Started Tornado on port {}...".format(port))
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()