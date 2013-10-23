/**
 * trcme module contains objects that manage trc.me client-side 
 * functionality.
 */
trcme = function () {
  /** Private */
  var my = {}; 

  /** Public */
  var that = {
  
    /** Configurable trc.me options */
    options: {
      zoom: 13, // Zoom level when sensor is false
      position: {
        // Center of map. Defaults to Cape Town.        
        coords: {
          latitude: -33.934103, 
          longitude: 18.380814,
          accuracy: 10.0 // Assuming location_type == ROOFTOP
        }
      }, 
      browserSupport: new Boolean(), // Browser has geolocation support
      sensor: new Boolean() // User used browser's geolocation
    },
    
    /** Functionality for specific pages or dialog boxes */
    dialog: {}
  }; 
   
  return that;
}();


/**
 * Utility functions
 */
trcme.util = function () {
  var my = {};

  var that = {

    /** Set placeholder text for older browsers */
    setPlaceholder: function (element, value) {
	  if (element.val() == '') {
        // Initial value
        element.css('color', 'grey');
        element.val(value);
	  }
      // On focus
      element.focus(function () {
        if ($(this).val() === value) {
          $(this).css('color', 'black');
          $(this).val('');
        }
      });
      // On blur
      element.blur(function () {
        if ($(this).val() === '') {
          $(this).css('color', 'grey');
          $(this).val(value);
        }
      });
    },

    /** Extract hash tags from text */
    extractHashtags: function (text) {
      result = text.match(/(#\w+)/g);
      if (result) {
        return result.join(' ');
      }
      return '';
    }
  };

  return that;
}();


/**
 * Functionality specific to the Update Tag page
 */
trcme.dialog.updateTag = function () {
  var my = {}; 

  var that = {
  
    /** Load Update Tag dialog asynchronously */
    load: function (code) {
	  // Strip initial "trc.me/" if the user put that in
	  var parse_code = /\/(\w{6,})\/?$/;
	  var result = parse_code.exec(code)
	  if (result) {
		  code = result[1];
	  }
      
      // We will need the code in onReady()
      my.code = code;
    
      // Load Gears in case we need it ...
      //$.getScript('http://code.google.com/apis/gears/gears_init.js');
      // ... asychronously
      $.ajax({
        async: false,
        url: 'http://code.google.com/apis/gears/gears_init.js',
        dataType: 'script'
      });
      // Fetch HTML for Update Tag dialog
      $.ajax({
        async: false,
        url: trcme.options.baseurl + 'ajax/' + code + '/',
        success: function (data, status, xhr) {
          $('#dialog').html(data);
        }
      });
      this.onReady();
    },
    
    /** Setter for code. If Update Tag requested directly, it must be set */
    setCode: function (code) {
      my.code = code;
    },
    
    /** Update Tag dialog onReady script */
    onReady: function () {
      if (!Modernizr.input.placeholder) {
        trcme.util.setPlaceholder($('input[name=address]'), 'Where is trc.me/' + my.code + '?');
      }
      
      // Get location
      if (Modernizr.geolocation) {
        $('#manual-entry').hide();
        trcme.options.browserSupport = true;
        navigator.geolocation.getCurrentPosition(
          trcme.maps.loadMarkerMap, 
          this.handleGeolocationError);
        
      } else if (google.gears) {
        // Try Google Gears
        $('#manual-entry').hide();
        trcme.options.browserSupport = true;
        var geo = google.gears.factory.create('beta.geolocation');
        geo.getCurrentPosition(
          trcme.maps.loadMarkerMap, 
          this.handleGeolocationError);
        
      } else {
        // No geolocation support
        trcme.options.browserSupport = false;
        trcme.maps.loadBlankMap();
      } 
    },
    
    /** Handles mobile requirements; no interactive map */
    mobileOnReady: function () {
      if (!Modernizr.input.placeholder) {
        trcme.util.setPlaceholder($('input[name=address]'), 'Where is trc.me/' + my.code + '?');
      }
    },
    
    handleGeolocationError: function (error) {
      if (error.code == 1) {
        // User said no. TODO: Perhaps record this. 
      }
      trcme.maps.loadBlankMap();
      $('#manual-entry').show();
    },
    
    centerMapOnAddress: function () {
      var geocoder = new google.maps.Geocoder();
      geocoder.geocode(
        { address: $('input[name="address"]').val() }, 
        trcme.maps.setPositionByGeocoder
      );
    },
    
    postForm: function () {
      if (trcme.options.position == null) {
        return false;
      }
      // Post form
      $('input[name="latitude"]').val(trcme.options.position.coords.latitude);
      $('input[name="longitude"]').val(trcme.options.position.coords.longitude);
      $('input[name="accuracy"]').val(trcme.options.position.coords.accuracy);
      $('input[name="geolocation_support"]').val(trcme.options.browserSupport);
      $('input[name="sensor"]').val(trcme.options.sensor);
      $('form').submit(); // Must be submitted in order to get the pic!
    }
    
  };
  
  return that;
}();


/**
 * Functionality specific to the Login form
 */
trcme.dialog.login = function () {
  var my = {}; 

  var that = {
  
    /**
     * Log in user asynchronously
     */
    loginRequest: function () {
      $.ajax({
        url: trcme.options.baseurl + 'ajax/login/',
        type: 'POST',
        data: { username: $('#authform input[name=username]').val(),
                password: $('#authform input[name=password]').val(),
                csrfmiddlewaretoken: $('#authform input[name=csrfmiddlewaretoken]').val() },
        dataType: 'json',
        success: this.callback
      });
    },
    
    registerRequest: function () {
      $.ajax({
        url: trcme.options.baseurl + 'ajax/register/',
        type: 'POST',
        data: { username: $('#registerform input[name=username]').val(),
                email: $('#registerform input[name=email]').val(),
                password1: $('#registerform input[name=password1]').val(),
                password2: $('#registerform input[name=password2]').val(),
                csrfmiddlewaretoken: $('#registerform input[name=csrfmiddlewaretoken]').val() },
        dataType: 'json',
        success: this.callback // Reuse callback
      });
    },
    
    callback: function (data, status, xhr) {
      if (data.success) {
        // Remove the login and registration forms
        $('#login_outer').remove(); 
        $('#register_outer').remove(); 
        // Update login status
        $('#login_status').html('<a href="' + trcme.options.baseurl + 'user/' + data.username + '/">' + data.username + '</a>');
        
        // Make for-users functionality visible
        $('.for_users').css('display', 'block');
      } else {
        // Login failed. Show error message
        $('.error').html(data.error);
      }
    },
    
    onReady: function () {
      if (Modernizr.input.placeholder) {
        // Using Django AuthenticationForm. Add placeholder attributes.
        //$('input[name=username]').attr('placeholder', 'Username');
        //$('input[name=password]').attr('placeholder', 'Password');
      } else {
        // Browser does not support placeholder attribute. Script it.
        trcme.util.setPlaceholder($('input[name=username]'), 'Username');
        trcme.util.setPlaceholder($('input[name=password]'), 'Password');
      }
    }
  };
  
  return that;
}();


/**
 * The register dialog 
 */
trcme.dialog.register = function () {
  var that = {
    onReady: function () {
      if (!Modernizr.input.placeholder) {
        trcme.util.setPlaceholder($('input[name=username]'), 'Username');
        trcme.util.setPlaceholder($('input[name=email]'), 'E-mail address');
        trcme.util.setPlaceholder($('input[name=password1]'), 'Password');
        trcme.util.setPlaceholder($('input[name=password2]'), 'Confirm password');
      }
    }
  };
  return that;
}();


/**
 * The search results dialog 
 */
trcme.dialog.search = function () {
  var that = {
    onReady: function () {
      if (!Modernizr.input.placeholder) {
        trcme.util.setPlaceholder($('input[name=q]'), 'Search for flags');
      }
    }
  };
  return that;
}();


/**
 * Functionality to change password
 */
trcme.dialog.chpwd = function () {
  var that = {

    /**
     * Change password asynchronously
     */
    request: function () {
      $.ajax({
        url: trcme.options.baseurl + 'ajax/chpwd/',
        type: 'POST',
        data: {
          old_password: $('#chpwd_form input[name=old_password]').val(),
          new_password1: $('#chpwd_form input[name=new_password1]').val(),
          new_password2: $('#chpwd_form input[name=new_password2]').val(),
          csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val() },
        dataType: 'json',
        success: this.callback
      });
    },

    callback: function (data, status, xhr) {
      if (data.success) {
        // Show confirmation
        $('.message').html('Password changed successfully');
      } else {
        // Login failed. Show error message
        $('.error').html(data.error);
      }
    },

    onReady: function () {
      if (Modernizr.input.placeholder) {
        // Placeholder text supported. Hide labels.
        $('label.noplaceholder').css('display', 'none');
      }
    }

  };

  return that;
}();


/** 
 * Applies to user_edit_dialog.html, which appears in user_home.html and
 * user_edit.html
 */
trcme.dialog.editUser = function () {
  var that = {
    onReady: function () {
      if (Modernizr.input.placeholder) {
        $('label.noplaceholder').css('display', 'none');
      }
    }
  };
  return that;
}();


/**
 * Manages static pages
 */
trcme.dialog.page = function () {
  var that = {
  
    /** Load page with specified slug */
    load: function (slug) {
      $('#dialog').css('overflow', 'scroll');
      $('#dialog').load(trcme.options.baseurl + 'page/' + slug + '/');
    }
    
  };
  
  return that;
}();


/**
 * Functionality related to the index page
 */
trcme.dialog.index = function () {
  var my = {}; 

  var that = {
    /** Load index page asynchronously */
    request: function () {
      $('#dialog').css('overflow', 'hidden');
      $.ajax({
        url: trcme.options.baseurl + 'ajax/',
        success: this.callback
      });
    },
    
    /** Show index HTML, call script for index HTML */
    callback: function (data, status, xhr) {
      $('#dialog').html(data);
      trcme.dialog.login.onReady();
      trcme.dialog.register.onReady();
      trcme.dialog.index.onReady();
    },
    
    /** Script required for index dialog */
    onReady: function () {
      if (!Modernizr.input.placeholder) {
        trcme.util.setPlaceholder($('input[name=code]'), 'Enter a tag to flag it');
        trcme.util.setPlaceholder($('input[name=q]'), 'Search for flags');
      }
    }

  };
  
  return that;
}();

/**
 * Functionality related to the side panel
 */
trcme.dialog.panel = function () {
  var my = {}; 

  var that = {
    /** Hide the side panel */
    hide: function () {
      if ($('#sidepanel_outer').css('display') == 'none') {
        return; // Nothing to do
      }
      $('.socnet_buttons').hide();
      $('#sidepanel_outer').effect(
        'slide', 
        {
          mode: 'hide', 
          complete: function () { 
            $('#dialogs_container').css('width', '228px'); 
            $('.hide_panel_icon').hide();
            $('.show_panel_icon').show();
          }
        }
      );
    },
    
    /** Called when the page should open with the panel hidden */
    hideByDefault: function () {
      $('#sidepanel_outer').hide();
      $('#dialogs_container').css('width', '228px'); 
      $('.hide_panel_icon').hide();
      $('.show_panel_icon').show();
    },
    
    /** Show the side panel */
    show: function () {
        if ($('#sidepanel_outer').css('display') == 'block') {
          return; // Nothing to do
        }
      $('#dialogs_container').css('width', '678px');
      // Hide social network buttons before sliding
      $('.socnet_buttons').hide(); 
      $('#sidepanel_outer').effect(
        'slide',
        {
          mode: 'show',
          complete: function () {
            $('.show_panel_icon').hide();
            $('.hide_panel_icon').show();
            $('.socnet_buttons').show();
          }  
        }
      );
    },
    
    /** Load panel with specified slug */
    load: function (slug) {
      /* $('#sidepanel').css('overflow', 'scroll'); */
      $('#sidepanel').load(trcme.options.baseurl + 'page/' + slug + '/');
      this.show();
    },
    
    /** Load info regarding flag into side panel */
    loadFlag: function (flagId) {
      $('#sidepanel').load(trcme.options.baseurl + 'ajax/flag/' + flagId + '/');
    }
    
  };
  
  return that;
}();

/**
 * Functionality specific to the New Tag page
 */
trcme.dialog.newTag = function () {
  var my = {}; 

  var that = {
    
    /** Load the New Tag dialog */
    load: function () {
      // Fetch HTML for New Tag dialog
      $.ajax({
        async: false,
        url: trcme.options.baseurl + 'ajax/new/',
        success: function (data, status, xhr) {
          $('#dialog').html(data);
        }
      });
      this.onReady();
    },
    
    /** Script required for the New Tag dialog */
    onReady: function () {
      // Take the panel out the way
      trcme.dialog.panel.hide();
      if (!Modernizr.input.placeholder) {
        // Placeholder text not supported. Script it.
        trcme.util.setPlaceholder($('textarea[name=description]'), 'Description');
      }
      // Script textarea maxlength
      // Thank you http://www.techley.net/jquery/textarea-maxlength-using-jquery.html
      $('textarea[maxlength]').keyup(function() {
        var max = parseInt($(this).attr('maxlength'));
        var text = $(this).val();
        var len = text.length;
        
        // Show the live count
        $('.char_count').text(parseInt(max - len) + ' characters remaining.').css('color', '#222222'); // body colour
        
        if (len >= max) {
          // Set count to 0 and change colour
          $('.char_count').text('0 characters remaining.').css('color', '#FF0000');
          // Truncate text
          $(this).val(text.substr(0, max));
        } 
      });
    }
    
  };
  
  return that;
}();


/**
 * Manages subscriptions
 */
trcme.sub = function () {
  var that = {
  
    /** Subscribe to updates to a tag */
    trackTag: function (tagId) {
      $('#tracking').load(trcme.options.baseurl + 'sub/tag/' + tagId + '/track/');
    },
    
    /** Unsubscribe to updates to a tag */
    untrackTag: function (tagId) {
      $('#tracking').load(trcme.options.baseurl + 'sub/tag/' + tagId + '/untrack/');
    },
    
    /** Subscribe to updates to a user */
    followUser: function (username) {
      $('#following').load(trcme.options.baseurl + 'sub/user/' + username + '/follow/');
    },
    
    /** Unsubscribe to updates to a user */
    unfollowUser: function (username) {
      $('#following').load(trcme.options.baseurl + 'sub/user/' + username + '/unfollow/');
    },
    
  };
  
  return that;
}();

