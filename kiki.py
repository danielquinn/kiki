#!/usr/bin/env python

import re
import sys

import requests

from bs4 import BeautifulSoup


class UnknownShipperException(Exception):
    pass


class Shipper(object):

    REGEX = None
    URL = None
    USER_AGENT = "Kiki (https://github.com/danielquinn/kiki)"
    HEADERS = {
        "User-Agent": USER_AGENT
    }

    def __init__(self, tracking_number):
        self.tracking_number = tracking_number

    def fetch(self):
        raise NotImplementedError()

    def parse(self, page):
        raise NotImplementedError()

    def where_is(self):
        info = self.parse(self.fetch())
        return info["location"]

    @classmethod
    def guess(cls, tracking_number):
        """
        Attempt to guess the right shipper based on the tracking number.
        :return an instance of a Shipper subclass
        """

        if Parcelforce.REGEX.match(tracking_number):
            return Parcelforce(tracking_number)

        if Eurodis.REGEX.match(tracking_number):
            return Eurodis(tracking_number)

        raise UnknownShipperException(
            "From the looks of that shipping number, it's hard to discern "
            "what the shipper is."
        )


class Eurodis(Shipper):

    REGEX = re.compile(r"^[0-9]{24}$")
    URL = "http://eurodis.com/track-trace?{id}"

    def fetch(self):
        url = self.URL.format(id=self.tracking_number)
        return requests.get(url, headers=self.HEADERS).text

    def parse(self, page):

        soup = BeautifulSoup(page, "html.parser")
        location_soup = soup\
            .find_all(class_="ship-history-content")[1]\
            .find_all("tr")[1]\
            .find_all("td")

        return {
            "location": "{date} {time}: {city}, {country} ({event})".format(
                date=location_soup[0].text,
                time=location_soup[1].text,
                city=location_soup[3].text,
                country=location_soup[2].text,
                event=location_soup[4].text,
            )
        }


class Parcelforce(Shipper):

    REGEX = re.compile("^[A-Z]{2}[0-9]{7}$")
    URL = "http://www.parcelforce.com/track-trace?trackNumber={id}"

    def fetch(self):
        url = self.URL.format(id=self.tracking_number)
        return requests.get(url, headers=self.HEADERS).text

    def parse(self, page):

        soup = BeautifulSoup(page, "html.parser")
        location_soup = soup\
            .find_all(class_="tracking-history")[0]\
            .find_all("tbody")[0]\
            .find_all("tr")[0]\
            .find_all("td")

        return {
            "location": "{date} {time}: {city} ({event})".format(
                date=location_soup[0].text,
                time=location_soup[1].text,
                city=location_soup[2].text,
                event=location_soup[3].text,
            )
        }

if __name__ == "__main__":
    location = Shipper.guess(sys.argv[1]).where_is()
    print("\n  It looks like your package is here:\n\n  {}\n".format(location))
