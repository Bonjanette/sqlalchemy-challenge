# Import dependencies
import datetime as dt
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
from datetime import datetime

def create_temp_stat_list(row_data):
    # Creates a list of temperature statistics for each date.
    temp_stat_list = []
    for date, min, avg, max in row_data:
        temp_dict = {}
        temp_dict['date'] = date
        temp_dict['min'] = min
        temp_dict['avg'] = avg
        temp_dict['max'] = max
        temp_stat_list.append(temp_dict)
    return(temp_stat_list)

#################################################
# Database Setup
#################################################
# create an engine for the hawaii database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return(
        f"<h1>Welcome to a Hawaii weather API!</h1><br/>"
        f"<h2>Available Routes include:</h2><br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return a list of dates and precipitation for the most recent year of data"""
    
    # Create a session link from Python to the DB
    session = Session(engine)
    precip_data = session.query(measurement.date, measurement.prcp).\
        filter(measurement.date >= dt.date(2017, 8, 23) - dt.timedelta(days=365)).all()
    session.close()

    # Create dictionary to store precipitation data
    precipitation_dict = {}
    for date, prcp in precip_data:
        precipitation_dict[date] = prcp

    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations"""
    # Create a session link from Python to DB, query data, and return results
    session = Session(engine)
    station_data = session.query(station.station.distinct()).all()
    session.close()
    # Create a list from the row data
    station_list = list(np.ravel(station_data))
    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def active_station_temps():
    """Return a list of temperature observations from most active station for 
        most recent year of data."""
    #Create session link from Python to DB, query data, and return results
    session = Session(engine)
    active_station_temp_data = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station == 'USC00519281').\
        filter(measurement.date >= dt.date(2017, 8, 23) - dt.timedelta(days=365)).all()
    session.close()
    # Create a dictionary from the row data and append to the list each date's data
    active_station_temp_list = []
    for date, temp in active_station_temp_data:
        station_date_dict = {}
        station_date_dict['date'] = date
        station_date_dict['temp'] = temp
        active_station_temp_list.append(station_date_dict)
    return jsonify(active_station_temp_list)

@app.route("/api/v1.0/<start_date>")
def start_temp_stats(start_date):
    """Return a list of min, avg, and max temperature for all dates greater than or equal
       to the client supplied start date""" 
    # use try/except to catch errors with the date and
    # return a message to client in the event of an error
    try:    
        date = datetime.strptime(start_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": f"Please use this date format: YYYY-MM-DD."})

    session = Session(engine)

    select = [measurement.date,
              func.min(measurement.tobs),
              func.avg(measurement.tobs),
              func.max(measurement.tobs)]
    start_temp_data = session.query(*select).filter(measurement.date >= date).\
            group_by(measurement.date).order_by(measurement.date)
        
    session.close()
    # Call function to get list containing temperature statistics for each date and
    # return to the client as a json list.
    start_temp_list = create_temp_stat_list(start_temp_data)
    return jsonify(start_temp_list)
    

@app.route("/api/v1.0/<start>/<end>")
def inclusive_temp_stats(start, end):
    """Return a list of min, avg, and max temperature for all dates between and including
       the client supplied start and end dates"""
    # Convert "start" and "end" to date type for querying, 
    # use try/except to catch any errors with the dates and
    # return a message to client in the event of an error
    try:
        date_start = datetime.strptime(start, '%Y-%m-%d').date()
        date_end = datetime.strptime(end, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": f"Please use this date format: YYYY-MM-DD."})
    
    session = Session(engine)
    # Query the temperature data from requested date range.
    select = [measurement.date,
              func.min(measurement.tobs),
              func.avg(measurement.tobs),
              func.max(measurement.tobs)]
    inclusive_temp_data = session.query(*select).\
            filter(measurement.date >= date_start).filter(measurement.date <= date_end).\
            group_by(measurement.date).order_by(measurement.date)
    
    session.close()
    # Call function to transform inclusive_temp_date into a jsonifiable list.
    inclusive_temp_list = create_temp_stat_list(inclusive_temp_data)
    return jsonify(inclusive_temp_list)
    
if __name__ == '__main__':
    app.run(debug=True)
    