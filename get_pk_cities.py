import pandas as pd
# df = pd.read_excel("worldcities.xlsx")
# cities = df[df['country']=='Pakistan']
file = open("pk_cities.txt","r")
# file.write(str(','.join(cities['city'].tolist())))
print(str(file.readlines()).split(","))
file.close()