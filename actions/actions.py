# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List, Optional, Tuple

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, UserUttered
from rasa_sdk.executor import CollectingDispatcher

import datetime
from pytz import timezone


LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


class ActionSetCurrentTimeWithTZ(Action):

    def name(self) -> Text:
        return "action_set_current_time_with_tz"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        current_time = f"{datetime.datetime.now().strftime('%H:%M:%S')}"

        return [
            SlotSet("current_time_with_tz", f"{current_time} ({LOCAL_TIMEZONE})")
        ]


def timezone_from_city(city: Optional[Text]) -> datetime.tzinfo:
    if not city:
        return LOCAL_TIMEZONE
    return {
        "berlin": timezone("Europe/Berlin"),
        "london": timezone("Europe/London"),
    }.get(city.lower(), LOCAL_TIMEZONE)


class ActionSetCurrentTimeInLastMentionedTZ(Action):

    def name(self) -> Text:
        return "action_set_current_time_in_last_mentioned_tz"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        last_mentioned_city = next(tracker.get_latest_entity_values("city"), None)
        print(f"last_mentioned_city = {last_mentioned_city}")
        timezone = timezone_from_city(last_mentioned_city)
        current_time = f"{datetime.datetime.now(timezone).strftime('%H:%M:%S')}"

        return [
            SlotSet("current_time_in_last_mentioned_tz", f"{current_time} ({timezone})")
        ]


class ActionSetCurrentTimeOfDay(Action):

    def name(self) -> Text:
        return "action_set_current_time_of_day"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        h: int = datetime.datetime.now().hour
        time_of_day: Optional[Text] = None
        if 4 <= h and h < 10:
            time_of_day = "morning"
        elif 10 <= h < 18:
            time_of_day = "day"
        elif 18 <= h < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        return [
            SlotSet("current_time_of_day", time_of_day)
        ]


def event_is_user_uttered_with_intent(event: Dict[Text, Any], intent: Text) -> bool:
    return (
        event.get("event", "") == "user" and
        event.get("parse_data", {}).get("intent", {}).get("name", "") == intent
    )


def event_is_action(event: Dict[Text, Any], action_name: Text) -> bool:
    return (
        event.get("event", "") == "bot" and
        event.get("metadata", {}).get("utter_action", "") == action_name
    )


class ActionSetNumTimesBotWasChallenged(Action):

    def name(self) -> Text:
        return "action_set_num_times_bot_was_challenged"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        num_times_bot_was_challenged = 0
        for event in tracker.applied_events():
            if event_is_user_uttered_with_intent(event, "bot_challenge"):
                num_times_bot_was_challenged += 1

        print(f"num_times_bot_was_challenged <= {num_times_bot_was_challenged}")
        return [
            SlotSet("num_times_bot_was_challenged", num_times_bot_was_challenged)
        ]


def get_entity_data(
    message: Dict[Text, Any]
) -> List[Tuple[Text, Any, float]]:
    return [
        (
            entity.get("entity", 1.0),
            entity.get("value", 1.0),
            entity.get("confidence_entity", 1.0),
        )
        for entity in message.get("entities", {})
    ]


class ActionSetLowEntityScore(Action):

    def name(self) -> Text:
        return "action_set_low_entity_score"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        for entity_type, value, score in get_entity_data(tracker.latest_message):
            print(f"entity score: {score} for {entity_type}: {value}")
            if score < 0.9:
                if entity_type == "city":
                    return [
                        SlotSet("low_entity_score", True),
                        SlotSet("problematic_city_name", value),
                        SlotSet("city", None),
                    ]
                else:
                    return [
                        SlotSet("low_entity_score", True),
                    ]

        return [
            SlotSet("low_entity_score", False),
        ]

