from flask import render_template, flash, request, url_for, redirect, session

from application import app, helpers


@app.route("/")
def home():
    background = helpers.set_default()
    return render_template('home.html', map=background._repr_html_())


@app.route("/roads")
def roads():
    roads_map = helpers.set_roads()
    return render_template('roads.html', map=roads_map._repr_html_())

@app.route("/pedestrian")
def pedestrian():
    pedestrian_roads_map = helpers.set_pedestrian()
    return render_template('pedestrian.html', map=pedestrian_roads_map._repr_html_())

@app.route("/ground")
def ground():
    ground_data = helpers.set_ground()
    return render_template('ground.html', map=ground_data._repr_html_())
