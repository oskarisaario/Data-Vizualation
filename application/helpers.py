import random
from requests import Request
import fiona
fiona.drvsupport.supported_drivers['WFS'] = 'r'

import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip

from application import wfs, wfs_url


# Available data layers
ski = list(wfs.contents)[2]         #Ladut
kkv = list(wfs.contents)[3]         #Katujen kunnossapito vastuualueet
ktl = list(wfs.contents)[4]         #Katujen toiminnalliset luokat
kpo = list(wfs.contents)[5]         #Kaupunginosat
border = list(wfs.contents)[6]      #Kaupunginraja
keski = list(wfs.contents)[7]       #Keskilinjat
kevyt = list(wfs.contents)[8]       #Kevytliikenne
maa = list(wfs.contents)[12]        #Maalajikekartta perus
postinum = list(wfs.contents)[18]      #Postinumeroalueet




#Background maps for all routes/layers
background = folium.Map(location=[60.293352, 25.037769], zoom_start=11, tiles='OpenStreetMap')
roads_map = folium.Map(location=[60.293352, 25.037769], zoom_start=11, tiles='OpenStreetMap')
pedestrian_roads_map = folium.Map(location=[60.293352, 25.037769], zoom_start=11, tiles='OpenStreetMap')
ground_data = folium.Map(location=[60.293352, 25.037769], zoom_start=11, tiles='OpenStreetMap')


#Set default map with city borders
def set_default():
   borders = get_url(border)
   folium.GeoJson(borders, name="Kaupungin raja").add_to(background)
   
   #Set options for layerControl
   get_kkv()
   get_skipaths()
   get_neighborhoods()
   get_postal()
   folium.LayerControl(collapsed=False).add_to(background)
   return background


#Set map and for road info
def set_roads():
   borders = get_url(border)
   folium.GeoJson(borders, name="Kaupungin raja").add_to(roads_map)
   get_ktl()
   get_centers()
   folium.LayerControl(collapsed=False).add_to(roads_map)
   return roads_map


#Set map for pedestrian roads and info
def set_pedestrian():
   borders = get_url(border)

   folium.GeoJson(borders, name="Kaupungin raja").add_to(pedestrian_roads_map)
   get_kevyt()
   folium.LayerControl(collapsed=False).add_to(pedestrian_roads_map)
   return pedestrian_roads_map


#Set map for ground/soil data
def set_ground():
   borders = get_url(border)

   folium.GeoJson(borders, name="Kaupungin raja").add_to(ground_data)
   get_maalajike()
   folium.LayerControl(collapsed=False).add_to(ground_data)
   return ground_data


#Get url for content
def get_url(content_name):
   params = dict(service='WFS', version=wfs.version, request='GetFeature',
   typeName=content_name, outputFormat='json')
   wfs_request_url = Request('GET', wfs_url, params=params).prepare().url
   try:
      data_map = gpd.read_file(wfs_request_url)
   except ValueError:
      return "Something went wrong"
   return data_map


#Get colors for groups and adds a column with color
def get_colors(gdf, group_by:str):
   fill_color = []
   groups = []
   for i  in gdf[group_by]:
      if i not in groups:
         groups.append(i)
         fill_color.append('#{:06x}'.format(random.randint(0, 256**3)))
   
   for index, row in gdf.iterrows():
      k = 0
      for i in groups:
         if row[group_by] == i:
            gdf.at[index, "fill_color"] = fill_color[k]
         else:
            k += 1
   return gdf


#Get ski paths
def get_skipaths():
   ski_map = get_url(ski)
   ski_map = ski_map.to_crs(4326)

   #Creates feature group for ski paths and markers
   ski_paths_feature = folium.FeatureGroup(name="Ladut", show=False)
   folium.GeoJson(data=ski_map, name="Ladut", style_function= lambda x: {"color" : "#FF0000", "opacity": 0.5}, tooltip=GeoJsonTooltip(fields=["type_name","name_fi", "street_address_fi"], aliases=["Tyyppi", "Nimi ja pituus", "Osoite"])).add_to(ski_paths_feature)
   ski_paths_feature.add_to(background)
   return background


#Get postalarea codes on map
def get_postal():
   postal_map = get_url(postinum)
   postal_map = postal_map.to_crs(4326)
   
   postal_feature = folium.FeatureGroup(name="Postinumeroalueet", show=False)
   postal_map = get_colors(postal_map, "postinumero")

   folium.GeoJson(postal_map,style_function=lambda x: {'fillColor':x['properties']['fill_color']}, tooltip=GeoJsonTooltip(
      fields=["id", "kunta", "kuntanro", "nimi", "postinumero", "postitoimipaikka"], aliases=["Id", "Kunta", "Kuntanumero", "Nimi", "Postinumero", "Postitoimipaikka"])).add_to(postal_feature)
   postal_feature.add_to(background)
   return background


#Get Street maintenance areas and info
def get_kkv():
   kkv_map = get_url(kkv)
   kkv_map = kkv_map.to_crs(4326)

   kkv_feature = folium.FeatureGroup(name="Katujen kunnossapito vastuualueet", show=False)
   fill_color = ["orange", "yellow", "red", "purple", "blue", "green", "gray", "brown", "pink"]
   kkv_map["fill_color"] = fill_color

   #Add markers to areas
   coords = kkv_map["geometry"].centroid
   kkv_map["long"] = coords.map(lambda p: p.x)
   kkv_map["lat"] = coords.map(lambda p: p.y)
   for i in range(len(kkv_map)):
      folium.Marker(location=[kkv_map["lat"][i], kkv_map["long"][i]], tooltip=f'Nimi: {kkv_map["nimi"][i]}<br>Kuvaus: {kkv_map["kuvaus"][i]}').add_to(kkv_feature)

   folium.GeoJson(kkv_map,style_function=lambda x: {'fillColor':x['properties']['fill_color']}).add_to(kkv_feature)
   kkv_feature.add_to(background)
   return background


#Get street classing
def get_ktl():
   ktl_map = get_url(ktl)
   ktl_map = ktl_map.to_crs(4326)

   ktl_features = folium.FeatureGroup(name="Tiet", show=False, control=False)
   folium.FeatureGroup(name="Tiet", show=False, control=False).add_to(roads_map)

   #Checks all classes and add different colours and color columns to each one
   ktl_map = get_colors(ktl_map, "luokka")

   #Groups by class and then creates layers for each group
   for grp_name, df_grp in ktl_map.groupby("luokka"):
      grp_name = folium.GeoJson(data=df_grp, name=grp_name + "(Katujen toiminnaliset luokat)", show=False, style_function= lambda x: {'color':x['properties']['fill_color'], "opacity": 0.5}).add_to(roads_map)
   return ktl_features


#Get neighborhoods
def get_neighborhoods():
   kpo_map = get_url(kpo)
   kpo_map = kpo_map.to_crs(4326)
   kpo_feature = folium.FeatureGroup(name="Kaupunginosat", show=False)
   
   #Creates a color column and gives random color value for each
   for x in kpo_map.index:
      fill_color = '#{:06x}'.format(random.randint(0, 256**3))
      kpo_map.at[x, "fill_color"] = fill_color
   
   #Add markers to areas
   coords = kpo_map["geometry"].centroid
   kpo_map["long"] = coords.map(lambda p: p.x)
   kpo_map["lat"] = coords.map(lambda p: p.y)
   for i in range(len(kpo_map)):
      folium.Marker(location=[kpo_map["lat"][i], kpo_map["long"][i]], tooltip=f'Nimi: {kpo_map["kosanimi"][i]}<br>{kpo_map["kosa_ruotsiksi"][i]}<br> Suuralue: {kpo_map["suuralue"][i]}').add_to(kpo_feature)
   
   folium.GeoJson(kpo_map,style_function=lambda x: {'fillColor':x['properties']['fill_color']}).add_to(kpo_feature)
   kpo_feature.add_to(background)
   return background


#Get centerlines (keskilinjat)
def get_centers():
   keski_map = get_url(keski)
   keski_map = keski_map.to_crs(4326)

   keski_feature = folium.FeatureGroup(name="Keskilinjat", show=False)
   keski_map = get_colors(keski_map, "luokka")

   #Groups by class and then creates layers for each group and adds tooltips with info about the road
   for grp_name, df_grp in keski_map.groupby("luokka"):
      grp_name = folium.GeoJson(data=df_grp, name=grp_name + "(Keskilinjat)" , show=False, style_function= lambda x: {'color':x['properties']['fill_color'], "opacity": 0.5},
                                 tooltip=folium.GeoJsonTooltip(fields=["nimi","luokka","taso", "paallyste", "suunta", "valaistu", "nopeusrajoitus", "kunnossapitoluokka", 
                                                                       "kaistanvaihto_kielletty", "jalankulku","pyoraily" ], aliases=["Nimi","Luokka","Taso", "Päällyste", "Suunta", "Valaistu",
                                                                        "Nopeusrajoitus", "Kunnossapitoluokka", "Kaistanvaihto kielletty", "Jalankulku", "Pyöräily"])).add_to(roads_map)
   return keski_feature


#Get pedestrian road info (kevytliikenne)
def get_kevyt():
   kevyt_map = get_url(kevyt)
   kevyt_map = kevyt_map.to_crs(4326)

   kevyt_feature = folium.FeatureGroup(name="Kevytliikenne", show=False)
   kevyt_map = get_colors(kevyt_map, "luokka")

   #Groups by class and then creates layers for each group and adds tooltips with info about the road
   for grp_name, df_grp in kevyt_map.groupby("luokka"):
      grp_name = folium.GeoJson(data=df_grp, name=grp_name + "(Kevytliikenne)" , show=False, style_function= lambda x: {'color':x['properties']['fill_color'], "opacity": 0.5},
                                 tooltip=folium.GeoJsonTooltip(fields=["luokka", "taso", "paallyste", "valaistu", "jalankulku","pyoraily" ], aliases=["Luokka", "Taso", "Päällyste",
                                 "Valaistu","Jalankulku", "Pyöräily"])).add_to(pedestrian_roads_map)
   return kevyt_feature


#Get ground/soil info
def get_maalajike():
   maalajike_map = get_url(maa)
   maalajike_map = maalajike_map.to_crs(4326)

   maalajike_map_feature = folium.FeatureGroup(name="Maanpeite -16", show=False)
   maalajike_map = get_colors(maalajike_map, "pintamaalaji")
   
   #Groups by class and then creates layers for each group and adds tooltips with info about the ground
   for grp_name, df_grp in maalajike_map.groupby("pintamaalaji"):
      grp_name = folium.GeoJson(data=df_grp, name=grp_name + "(Maalajike)" , show=False, style_function= lambda x: {'color':x['properties']['fill_color'], "opacity": 0.5},
                                 tooltip=folium.GeoJsonTooltip(fields=["pintamaalaji", "pohjamaalaji", "teksti1", "teksti2"], aliases=["Pintamaalaji", "Pohjamaalaji", "Teksti-1", "Teksti-2"])).add_to(ground_data)
   
   return maalajike_map_feature

