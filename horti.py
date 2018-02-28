#!/usr/bin/python3

import os
import json
import sys
from datetime import datetime
import textwrap

# returns the input string with the specified length by cropping and padding
# the padding parameter should be a single character
def setStrLen(string, length, padding=' '):
    string = string[:length]
    if len(string) < length:
        string += padding*(length-len(string))
    return string



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
    
    def getPlotLinesFromJson(self, filename):
        with open(filename) as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError:
                return None
        
        # based on archangelic's code for pinhook
        # https://github.com/archangelic/pinhook-tilde/blob/master/plugins/watered.py
        if "last_watered" in data:
            last_watered = datetime.utcfromtimestamp(data['last_watered'])
            water_diff = datetime.now() - last_watered
        else:
            water_diff = 0
        
        art = self.getArt(data['description'], data.get('is_dead', False) and water_diff.days >= 5)
        
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
        
        return plotlines
    
    def loadPlantData(self):
        allData = []
        for user in os.listdir(self.config['userdir']):
            plantpath = os.path.join(self.config['userdir'], user, self.config['plantdata'].format(user=user))
            if os.path.isfile(plantpath):
                plotlines = self.getPlotLinesFromJson(plantpath)
                if plotlines:
                    allData.append(plotlines)
        return allData
    
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
