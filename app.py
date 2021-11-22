import numpy as np
import pandas as pd
import sqlalchemy
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Station = Base.classes.station
Measurement = Base.classes.measurement
session = Session(engine)
#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
#Create home page with urls
@app.route("/")
def welcome():
	"""List all available api routes."""
	return (
		f"Available Routes:<br/>"
		f"/api/v1.0/precipitation<br/>"
		f"/api/v1.0/stations<br/>"
		f"/api/v1.0/tobs<br/>"
		f"/api/v1.0/<start><br/>"
		f"/api/v1.0/<start>/<end>"
  )
	

#Convert the query results to a dictionary using `date` as the key and `prcp` as the value.

#Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation")    
def precipitation():
	session = Session(engine)
	last_yr = dt.date(2017,8,23) - dt.timedelta(days = 365)
	last_day = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
	results = session.query(Measurement.date, Measurement.prcp).\
	filter(Measurement.date > last_yr).order_by(Measurement.date).all()
	#Create precipitation list from queried data
	precipitation_list = []
	for date, prcp in results:
		data_dict = {}
		data_dict['date'] = date
		data_dict['prcp'] = prcp
		precipitation_list.append(data_dict)
	return jsonify(precipitation_list)


#Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():
#Return a JSON list of stations from the dataset.
	session = Session(engine)
	station_call = session.query(Station.station).all()
	station_list = list(np.ravel(station_call))
	return jsonify(station_list)
	session.close()

#Query the dates and temperature observations of the most active station for the last year of data.
#Return a JSON list of temperature observations (TOBS) for the previous year.
@app.route("/api/v1.0/tobs")

def tobs():
	session = Session(engine)
	#Obtain last data in the sqlite
	last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
	last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")
	first_date = last_date - dt.timedelta(days = 365)
	most_active_stations = (session.query(Measurement.station, func.count(Measurement.station)).\
	group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all())
	most_active_station = most_active_stations[0][0]
	#return	jsonify(most_active_station) Just used for verification of getting correct station
	tobs_results = session.query(Measurement.station, Measurement.tobs).\
	filter(Measurement.date.between(first_date, last_date)).filter(Measurement.station == most_active_station).all()
	tobs_list = []
	#Create dictionary for stations and temperatures in tobs_dict
	for station, tobs in tobs_results:
	   tobs_dict = {}
	   tobs_dict["station"] = station
	   tobs_dict["tobs"] = round(float(tobs),2)
	   tobs_list.append(tobs_dict)                             
	return jsonify(tobs_list)
	session.close()
#Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.

#When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date.

#When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive.

@app.route("/api/v1.0/<start>")
	
def start_day(start):
	"""Fetch the minimun, average and maximum temperature for the dates
		greater or equal to the start date, or a 404 if not."""

	start_day_list = []
	session = Session(engine)
 #Get last date in the data set
	last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
	last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")
 #Get first date in the data set
	initial_date = session.query(Measurement.date).order_by(Measurement.date.asc()).first().date
	initial_date = dt.datetime.strptime(initial_date, "%Y-%m-%d")
 #Define sel for temperature query
	sel=[Measurement.date,func.min(Measurement.tobs),func.max(Measurement.tobs), func.avg(Measurement.tobs)]
	response_temps = session.query(*sel).filter(Measurement.date >= start).all()
	session.close()
#Set start_date = start
	start_date = start
#Set start_date into date time format
	start_date = dt.datetime.strptime(start_date,"%Y-%m-%d")
	min_max_dict = (f"error: Please enter date between:" + str(initial_date) + "and" + str(last_date) + "in the format YYYY-MM-DD"), 404
#Check if correct dates are entered and display data	
	for temps in response_temps:
		if (start_date >= initial_date and start_date <= last_date):
			min_max_dict = {}
			min_max_dict = {
				"Start Date": start,
				"Temperature Min:": response_temps[0][1],
				"Temperature Max": response_temps[0][2],
				"Temperature Mean:": round(response_temps[0][3],2),
				"End Date": last_date
				}
		# Return JSON List of Min Temp, Avg Temp and Max Temp for a Given Start Range
		return jsonify(min_max_dict)
	else:    
		return min_max_dict

@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):
	#Get last date in the data set
	last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
	last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")
 	#Get first date in the data set
	initial_date = session.query(Measurement.date).order_by(Measurement.date.asc()).first().date
	initial_date = dt.datetime.strptime(initial_date, "%Y-%m-%d")
 	#Define sel for temperature query
	sel=[Measurement.date,func.min(Measurement.tobs),func.max(Measurement.tobs), func.avg(Measurement.tobs)]
	response_temps = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
	session.close()
	#Set start_date = start
	start_date = start
	start_date = dt.datetime.strptime(start_date,"%Y-%m-%d")
	#Set end_date = date
	end_date = end
	end_date = dt.datetime.strptime(end_date,"%Y-%m-%d")
	min_max_dict = (f"error: Please enter start and end date between:" + str(initial_date) + " and " + str(last_date) + " in the format YYYY-MM-DD end date should be greater than start date"), 404
	#Check if correct dates are entered and display data 
	for temps in response_temps:
	
		if (start_date >= initial_date and start_date <= last_date and end_date >= start_date):
			min_max_dict = {}
			min_max_dict = {
				"Start Date": start,
				"Temperature Min:": response_temps[0][1],
				"Temperature Max": response_temps[0][2],
				"Temperature Avg:": round(response_temps[0][3],2),
				"End Date": end
				}
		# Return JSON List of Min Temp, Avg Temp and Max Temp for a Given Start and End Range
		return jsonify(min_max_dict)
	else:    
		return min_max_dict
	
#Define main behaviour
if __name__ == '__main__':
	app.run(debug=True)
