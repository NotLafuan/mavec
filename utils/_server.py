from flask import Flask, render_template, Response, jsonify, request
import numpy as np
import cv2

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


def flask_app():
    app.run(host='0.0.0.0', debug=False, port="5000")
