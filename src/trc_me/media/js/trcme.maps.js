/**
 * maps object manages map-related functionality
 */
trcme.maps = function () {
  var my = {}; 

  var that = {
    
    /** Load Google Maps API script, sensor true */
    loadMarkerMap: function (position) {
      trcme.options.sensor = true;
      // Save position
      trcme.options.position.coords.latitude = position.coords.latitude;
      trcme.options.position.coords.longitude = position.coords.longitude;
      trcme.options.zoom = 15;
      
      var script = document.createElement("script");
      script.type = "text/javascript";
      script.src = "http://maps.google.com/maps/api/js?v=3.2&sensor=true&callback=trcme.maps.initialiseMarkerMap";
      document.body.appendChild(script);
    },
    
    /** Initialise marker map */
    initialiseMarkerMap: function () {
      var latLng = new google.maps.LatLng(
        trcme.options.position.coords.latitude, 
        trcme.options.position.coords.longitude);
      var mapOptions = {
        center: latLng,
        zoom: trcme.options.zoom,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      };
      trcme.maps.map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);
      // Add a marker at the centre
      this.addMarker(latLng);
    },
    
    /** Load Google Maps API script, sensor false */
    loadBlankMap: function () {
      var script = document.createElement("script");
      script.type = "text/javascript";
      script.src = "http://maps.google.com/maps/api/js?v=3.2&sensor=false&callback=trcme.maps.initialiseBlankMap";
      document.body.appendChild(script);
    },
    
    /** Initialise blank map */
    initialiseBlankMap: function () {
      // Default position (Cape Town Altantic coast puts dialog over ocean)
      var latLng = new google.maps.LatLng(
        trcme.options.position.coords.latitude, 
        trcme.options.position.coords.longitude);
      var mapOptions = {
        center: latLng,
        zoom: trcme.options.zoom,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      };
      trcme.maps.map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);
    },
    
    loadFlagMap: function (position) {
      // Save position
      trcme.options.sensor = false;
      trcme.options.position.coords.latitude = position.coords.latitude;
      trcme.options.position.coords.longitude = position.coords.longitude;
      trcme.options.zoom = 15;
        
      var script = document.createElement("script");
      script.type = "text/javascript";
      script.src = "http://maps.google.com/maps/api/js?v=3.2&sensor=false&callback=trcme.maps.initialiseFlagMap";
      document.body.appendChild(script);
    },

    initialiseFlagMap: function () {
      // Center map on saved position
      var latLng = new google.maps.LatLng(
        trcme.options.position.coords.latitude, 
        trcme.options.position.coords.longitude);
      var mapOptions = {
        center: latLng,
        zoom: trcme.options.zoom,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      };
      trcme.maps.map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);
      // Add a single flag at the centre
      this.addFlag(latLng);
    },
        
    /** Handle changes in marker position */
    markerPositionListener: function () {
      var latLng = trcme.maps.marker.getPosition();
      trcme.options.position.coords.latitude = latLng.lat();
      trcme.options.position.coords.longitude = latLng.lng();
      if (console) {
        console.debug(trcme.options.position.coords.latitude + ', ' + trcme.options.position.coords.longitude);
      }
    },
  
    /**
     * Load map showing one or more flags
     * 
     * @param flags Array of lat, long pairs
     */ 
    loadFlagsMap: function (flags) {
      if (flags.length == 0) {
        this.loadBlankMap();
        return;
      }
      if (flags.length == 1) {
        var position = {
          coords: {
            latitude: flags[0][0], 
            longitude: flags[0][1]
          }
        }
        // TODO: Refactor load*Map functions.
        this.loadFlagMap(position);
        return;
      }
      trcme.maps.flags = flags;
      var script = document.createElement("script");
      script.type = "text/javascript";
      script.src = "http://maps.google.com/maps/api/js?v=3.2&sensor=false&callback=trcme.maps.initialiseFlagsMap";
      document.body.appendChild(script);
    },
    
    /** Plot markers on map for flags */
    initialiseFlagsMap: function () {
      var sw_lat = (trcme.maps.flags[0][0] < trcme.maps.flags[1][0]) ? trcme.maps.flags[0][0] : trcme.maps.flags[1][0];
      var sw_lng = (trcme.maps.flags[0][1] < trcme.maps.flags[1][1]) ? trcme.maps.flags[0][1] : trcme.maps.flags[1][1];
      var sw = new google.maps.LatLng(sw_lat, sw_lng);
      var ne_lat = (trcme.maps.flags[0][0] > trcme.maps.flags[1][0]) ? trcme.maps.flags[0][0] : trcme.maps.flags[1][0];
      var ne_lng = (trcme.maps.flags[0][1] > trcme.maps.flags[1][1]) ? trcme.maps.flags[0][1] : trcme.maps.flags[1][1];
      var ne = new google.maps.LatLng(ne_lat, ne_lng);
      trcme.maps.bounds = new google.maps.LatLngBounds(sw, ne);
      
      for (i = 2; i < trcme.maps.flags.length; i++) {
        var latLng = new google.maps.LatLng(
          trcme.maps.flags[i][0], 
          trcme.maps.flags[i][1]);
        trcme.maps.bounds.extend(latLng);
      }
      var mapOptions = {
        center: trcme.maps.bounds.getCenter(),
        zoom: 13,
        mapTypeId: google.maps.MapTypeId.ROADMAP
      };
      trcme.maps.map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);
      trcme.maps.map.fitBounds(trcme.maps.bounds);
      
      for (i = 0; i < trcme.maps.flags.length; i++) {
        var latLng = new google.maps.LatLng(
          trcme.maps.flags[i][0], 
          trcme.maps.flags[i][1]);
        this.addFlag(latLng);
      }
      
    },
    
    /** Create a trc.me Google Maps marker icon */
    createIcon: function () {
      // TODO: Reduce image size
      trcme.maps.icon = {
        image: new google.maps.MarkerImage(
          'http://media.trc.me/trc_me/img/marker_image.png',
          new google.maps.Size(94,85), // size
          new google.maps.Point(0, 0), // origin
          new google.maps.Point(15, 80)), // anchor
        shadow: new google.maps.MarkerImage(
          'http://media.trc.me/trc_me/img/marker_shadow.png',
          new google.maps.Size(94,85),
          new google.maps.Point(0, 0),
          new google.maps.Point(15, 80)),
        shape: {
          coord: [2, 15,
                  26, 3,
                  57, 3,
                  57, 29,
                  38, 35,
                  25, 33,
                  6, 47,
                  19, 78,
                  17, 82,
                  10, 80,
                  10, 73,
                  2, 46],
          type: 'poly'
        }
      };
    },
    
    /** Add a static flag to the map */
    addFlag: function (latLng) {
      if (!trcme.maps.icon) {
        this.createIcon();
      }
      var markerOptions = {
        icon: trcme.maps.icon.image,
        shadow: trcme.maps.icon.shadow,
        shape: trcme.maps.icon.shape,
        //title: '..', // TODO: Nice to have
        map: trcme.maps.map,
        position: latLng,
        draggable: false
      };
      var marker = new google.maps.Marker(markerOptions);
    },
    
    /** Add a draggable marker to the map */
    addMarker: function (latLng) {
      if (!trcme.maps.icon) {
        this.createIcon();
      }
      var markerOptions = {
        icon: trcme.maps.icon.image,
        shadow: trcme.maps.icon.shadow,
        shape: trcme.maps.icon.shape,
        //title: '...', // TODO: Nice to have
        map: trcme.maps.map,
        position: latLng,
        draggable: true
      };
      trcme.maps.marker = new google.maps.Marker(markerOptions);
      // Attach listeners to marker events
      google.maps.event.addListener(trcme.maps.marker, 'position_changed', this.markerPositionListener);
      //google.maps.event.addListener(trcme.maps.marker, 'dragend', this.markerPositionListener); // Redundant
    },
    
    /** Pan to new center */
    panTo: function (lat, lng) {
        var latLng = new google.maps.LatLng(lat, lng);
        trcme.maps.map.panTo(latLng);
    },
    
    /** Set position from geocoded address */
    setPositionByGeocoder: function (results, status) {
      if (status == google.maps.GeocoderStatus.OK) {
        trcme.options.position = {
          coords: {
            latitude: results[0].geometry.location.lat(),
            longitude: results[0].geometry.location.lng(),
            accuracy: 10.0 // Assuming location_type == ROOFTOP
          }
        }
        if (results[0].geometry.location_type != 'ROOFTOP') {
          trcme.options.position.coords.accuracy = 100.0;
        }
        
        // Pan to new centre
        trcme.maps.panTo(
          trcme.options.position.coords.latitude, 
          trcme.options.position.coords.longitude);
        // Move marker
        var latLng = new google.maps.LatLng(
          trcme.options.position.coords.latitude, 
          trcme.options.position.coords.longitude);
        // Add a marker at the centre
        if (trcme.maps.marker) {
          trcme.maps.marker.setPosition(latLng);
        } else {
          trcme.maps.addMarker(latLng);
        }
        
      } else {
        // Google can't find the address
        trcme.options.position = null;
        if (console) {
          console.log('No results found: ' + status);
        }
      }
    }
    
  }; 
   
  return that;
}();
