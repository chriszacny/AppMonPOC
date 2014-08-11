#AppMonPOC
=========

This is a very simple proof of concept I put together for application monitoring on a large screen device such as a TV.

The thought is, it would be composed of large modular "blocks" that can be resized and moved around. 

In addition, charts can be included to display messaging rates and such.

I used gridster.js to handle the blocks and resizing. I used highcharts.js for the charting. 

The client maintains a WebSocket connection to the server, which in this implementation is a Python Tornado server.

As a final note, this is meant to be conceptual... there is no error handling, things are hard-coded, no thread locking, etc. In practice, these things would all be done in a production application.

#Installation / Usage:
You will need to:

1. Install Python 3
2. Use pip to install tornado (pip install tornado)
3. Start the tornado server in the webserver directory (python demo_server.py)
4. Launch index.html in the client folder
