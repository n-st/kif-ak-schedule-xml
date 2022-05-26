#!/usr/bin/env python3
# encoding: utf-8 (as per PEP 263)

import sys
import requests
import json
import jinja2
from datetime import datetime as dt
import datetime

def log_debug(s):
    sys.stderr.write('%s\n' % s)

class APIInstance(object):
    def __init__(self, slug):
        self.slug = slug
        self.ak_slots = []
        self.aks = {}
        self.rooms = {}
        self.owners = {}
        self.categorys = {}
        self.tracks = {}

    def get_akslots(self):
        if self.ak_slots:
            return self.ak_slots
        else:
            log_debug('Fetching AK slots...')
            response = requests.get("https://ak.kif.rocks/%s/api/akslot/" % (self.slug))
            response.raise_for_status()
            self.ak_slots = response.json()
            for i in range(len(self.ak_slots)):
                if self.ak_slots[i]['start']:
                    self.ak_slots[i]['start'] = dt.strptime(self.ak_slots[i]['start'], '%Y-%m-%dT%H:%M:%S%z')
                if self.ak_slots[i]['updated']:
                    self.ak_slots[i]['updated'] = dt.strptime(self.ak_slots[i]['updated'], '%Y-%m-%dT%H:%M:%S.%f%z')
                if self.ak_slots[i]['duration']:
                    self.ak_slots[i]['duration'] = datetime.timedelta(hours=float(self.ak_slots[i]['duration']))
                    hours, remainder = divmod(self.ak_slots[i]['duration'].total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    self.ak_slots[i]['duration_str'] = '%d:%02d' % (hours, minutes)
                self.get_room(self.ak_slots[i]['room'])
            return self.ak_slots

    def _get_it(self, it_type, its, it_id):
        if not it_id:
            return {}
        if it_id in its:
            return its[it_id]
        else:
            log_debug('Fetching %s/%d...' % (it_type, it_id))
            response = requests.get("https://ak.kif.rocks/%s/api/%s/%d/" % (self.slug, it_type, it_id))
            response.raise_for_status()
            its[it_id] = response.json()
            return its[it_id]


    def get_ak(self, ak_id):
        ak = self._get_it('ak', self.aks, ak_id)
        for owner in ak['owners']:
            self.get_owner(owner)
        self.get_category(ak['category'])
        self.get_track(ak['track'])

    def get_room(self, room_id):
        return self._get_it('room', self.rooms, room_id)

    def get_owner(self, owner_id):
        return self._get_it('akowner', self.owners, owner_id)

    def get_category(self, category_id):
        return self._get_it('akcategory', self.categorys, category_id)

    def get_track(self, track_id):
        return self._get_it('aktrack', self.tracks, track_id)

def main():
    slug = 'kif500'

    with open('schedule.xml.j2') as file_:
        template = jinja2.Template(file_.read())

    api = APIInstance(slug)
    for slot in api.get_akslots():
        api.get_ak(slot['ak'])
        api.get_room(slot['room'])

    first_slot = min([x['start'] for x in api.ak_slots if x['start']])
    first_day = datetime.date(year=first_slot.year,
            month=first_slot.month,
            day=first_slot.day,
            )
    last_slot = max([x['start'] for x in api.ak_slots if x['start']])
    last_day = datetime.date(year=last_slot.year,
            month=last_slot.month,
            day=last_slot.day,
            )

    days = [first_day + datetime.timedelta(days=x) for x in range(0, (last_day-first_day).days+1)]

    msg = template.render(
            conf_title='KIF 50.0',
            conf_slug='kif500',
            days=days,
            slots=api.ak_slots,
            aks=api.aks,
            rooms=api.rooms,
            owners=api.owners,
            categories=api.categorys,
            tracks=api.tracks,
            conf_start=first_day,
            conf_end=last_day,
            conf_days=len(days),
            )

    # remove empty lines
    lines = msg.split('\n')
    lines = [line for line in lines if line.strip()]
    msg = '\n'.join(lines)

    print(msg)


"""
    akslot:
      {
        "id": 615,
        "start": "2022-05-26T09:00:00+02:00",
        "duration": "1.50",
        "fixed": false,
        "updated": "2022-05-26T03:29:53.735542+02:00",
        "ak": 528,
        "room": 139,
        "event": 7
      },

    ak:
    {
        "id": 528,
        "name": "Fachschaftswochenende/-tagung",
        "short_name": "FSWE-Austausch",
        "description": "An unserer Uni findet in der Regel zu Beginn und gegen Ende jeder Legislatur je ein (produktives) Fachschaftswochenende statt (wir fahren irgendwo hin und planen bzw. reflektieren die Legislatur). Mich interessiert ob es sowas auch an anderen Unis gibt und wie ihr sowas gestaltet.\r\nFolgende Fragestellungen möchte ich diskutieren:\r\n* Was ist das?\r\n* Macht das Sinn?\r\n* Wie gestaltet man sowas?\r\n* Was könnte man machen*\r\n* Wer kommt mit? Nur der Fachschaftsrat oder auch andere Aktive?",
        "link": "https://wiki.kif.rocks/wiki/KIF500:Fachschaftswochenende/-tagung",
        "protocol_link": "https://md.kif.rocks/fswe",
        "reso": false,
        "present": true,
        "notes": "",
        "interest": 30,
        "interest_counter": 0,
        "category": 24,
        "track": 27,
        "event": 7,
        "owners": [
          308
        ],
        "tags": [
          232
        ],
        "requirements": [],
        "conflicts": [
          526,
          529
        ],
        "prerequisites": []
      }
"""


if __name__ == '__main__':
    main()
