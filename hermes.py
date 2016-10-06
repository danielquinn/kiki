#!/usr/bin/env python

import requests
import sys

from bs4 import BeautifulSoup


class Shipper(object):

    URL = ""

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
        return Eurodis(tracking_number)


class Eurodis(Shipper):

    URL = "http://eurodis.com/track-trace?{id}"

    def fetch(self):
        return requests.get(self.URL.format(id=self.tracking_number)).text

    def parse(self, page):

        soup = BeautifulSoup(page, "html.parser")
        location_soup = soup\
            .find_all(class_="ship-history-content")[1]\
            .find_all("tr")[1]\
            .find_all("td")

        return {
            "location": "{} {}: {}, {} ({})".format(
                location_soup[0].text,
                location_soup[1].text,
                location_soup[2].text,
                location_soup[3].text,
                location_soup[4].text,
            )
        }


if __name__ == "__main__":
    location = Shipper.guess(sys.argv[1]).where_is()
    print("It looks like your package is here:\n\n  {}".format(location))
