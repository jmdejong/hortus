#!/usr/bin/python3

import os
import json
import sys
from datetime import datetime
import textwrap
import time

# returns the input string with the specified length by cropping and padding
# the padding parameter should be a single character
def setStrLen(string, length, padding=' '):
    string = string[:length]
    if len(string) < length:
        string += padding*(length-len(string))
    return string

def loadJsonFile(fname):
    try:
        with open(fname) as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError as e:
                return None
    except OSError as e:
        return None
    return data

def calculateLastWatered(last_watered, visitors):
    guest_timestamps = []
    for visitor in visitors:
        if not isinstance(visitor, dict):
            continue
        timestamp = visitor.get("timestamp")
        if not isinstance(timestamp, int):
            continue
        if timestamp <= int(time.time()):
            guest_timestamps.append(timestamp)
    
    all_timestamps = [last_watered] + guest_timestamps
    all_timestamps.sort()
    # calculate # of days between each guest watering
    timestamp_diffs = [(j-i)/86400.0 for i, j in zip(all_timestamps[:-1], all_timestamps[1:])]
    # plant's latest timestamp should be set to last timestamp before a
    # gap of 5 days
    # TODO: this considers a plant watered only on day 1 and day 4 to be
    # watered for all 4 days - need to figure out how to only add score
    # from 24h after each watered timestamp
    last_valid_element = next((x for x in timestamp_diffs if x > 5), None)
    if not last_valid_element:
        # all timestamps are within a 5 day range, can just use latest one
        return all_timestamps[-1]
    last_valid_index = timestamp_diffs.index(last_valid_element)
    # slice list to only include up until a >5 day gap
    valid_timestamps = all_timestamps[:last_valid_index + 1]
    return valid_timestamps[-1]
    

class Horti:
    
    def __init__(self, configFile):
        
        with open(configFile) as f:
            
            self.config = json.load(f)
        
    
    def getArt(self, description, dead=False):
        # Will I need to make a complete language parser?
        # keywords are space separated, but can contain spaces (venus flytrap)
        # some keywords are part of others (seed and seed-bearing)
        
        if dead:
            artFileName = self.config['deadart']
            
        else:
            stage = ''
            for s in self.config['stages']:
                if s in description and len(s) > len(stage):
                    stage = self.config['stages'][s]
            
            species = ''
            for s in self.config['species']:
                if s in description and len(s) > len(species):
                    species = self.config['species'][s]
            
            
            # colour and mutations could easily be added here
            
            artFileName = stage.format(species=species)
        
        try:
            with open(os.path.join(self.config['artdirectory'], artFileName)) as artfile:
                art = artfile.read()
        except OSError:
            return ""
        
        return art
    
    def getPlotLinesFromJson(self, user):
        plantpath = os.path.join(self.config['userdir'], user, self.config['plantdata'].format(user=user))
        data = loadJsonFile(plantpath)
        if not isinstance(data, dict):
            return None
        visitorpath = os.path.join(self.config['userdir'], user, self.config['visitordata'])
        visitors = loadJsonFile(visitorpath)
        if not isinstance(visitors, list):
            visitors = []
        
        
        last_watered = data.get("last_watered")
        description = data.get("description")
        owner = data.get("owner")
        is_dead = data.get('is_dead', False)
        if not (isinstance(last_watered, int) and isinstance(description, str) and isinstance(owner, str) and isinstance(is_dead, bool)):
            return None
        
        last_watered = calculateLastWatered(last_watered, visitors)
        
        time_delta_watered = int(time.time()) - last_watered
        if time_delta_watered > (5 * (24 * 3600)):
            is_dead = True
        if user == "abraxas":
            is_dead = False
        art = self.getArt(description, is_dead)
        
        width = self.config['plotwidth']
        
        artlines = art.split('\n')
        
        plotlines = []
        
        for i in range(self.config['plotheight']-self.config['descriptionheight']):
            line = artlines[i] if i<len(artlines) else ''
            line = setStrLen(line, width)
            plotlines.append(line)
        
        plotlines.append(setStrLen(data['owner'], width))
        
        descriptionlines = textwrap.wrap(data['description'], width)
        for i in range(self.config['descriptionheight']-1):
            line = descriptionlines[i] if i<len(descriptionlines) else ''
            line = setStrLen(line, width)
            plotlines.append(line)
        
        return plotlines, last_watered
    
    def loadPlantData(self):
        allData = []
        for user in os.listdir(self.config['userdir']):
            if user in self.config["banned"]:
                continue
            plantData = self.getPlotLinesFromJson(user)
            if plantData:
                allData.append(plantData)
        allData.sort(key=lambda d: -d[1])
        return [d[0] for d in allData]
    
    def toString(self, data):
        
        data = self.loadPlantData()
        
        string = ''
        
        startplot = 0
        while startplot < len(data):
            for y in range(self.config['plotheight']):
                for plotcol in range(self.config['plotshor']):
                    plot = startplot + plotcol
                    if plot >= len(data):
                        break
                    string += ' ' + data[plot][y]
                string += '\n'
            string += '\n'
            startplot += self.config['plotshor']
        
        return string




if __name__ == "__main__":
    if len(sys.argv)>1:
        config = sys.argv[1]
    else:
        config = os.path.join(sys.path[0], 'config.json')
    
    h = Horti(config)
    print(h.toString(h.loadPlantData()))
