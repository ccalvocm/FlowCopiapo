var scenario = (function() {

    var IS_IE = /*@cc_on!@*/false || !!document.documentMode;

    // PROGRESS BAR

    var progress = function() {

        var INTERVAL = 5000; //5s

        var timer = null;

        function update(percentage, description) {
            $('#progress-bar-description').html(description);
            $('#progress-bar-inner').css('width', percentage.toString()+'%');
        };

        function show(request) {
            if (timer == null) {
                update(0.0, '');
                request();
                $('#progress-bar-div').show(1);
                timer = setInterval(request, INTERVAL);
            }
        };

        function hide() {
            if (timer != null) {
                clearTimeout(timer);
                timer = null;
                $('#progress-bar-div').hide(1);
            }
        };

        return {
            update: update,
            show: show,
            hide: hide
        };
    }();

    // ON LOAD

    function initialise_main() {
        $('#spinner-div').show();
        $('.progress .progress-bar').progressbar();//Init Progress Bar
        $.fn.bootstrapBtn = $.fn.button.noConflict();//Hack to fix Bootstrap/JQuery-UI incompatibility

        charting.register_chart_plugins();

        scenario.get_scenario_metadata(function(name, desc, lat, lon, zoom) {
            map_base_manager.initialise_map(lat, lon, zoom);
            feature_finder.initialise_feature_finder(function() {
                map_layer_manager.initialise_layers();
            });
            scenario.get_simulation_dates();
            model_inputs.initialise_inputs();
            model_outputs.initialise_outputs();
            $('#spinner-div').hide();
        });
        // Complete the FIRST call to an endpoint before any additional ones so as to ensure the session cookie is set for the subsequent calls
        // This is because the first call prompts the creation of the session ID which the subsequent calls will need

        // Setup global jsPanel Closed event handler
        document.addEventListener('jspanelclosed', function(event) {
            layer_data_dialogs.layer_data_dialog_closed(event);
        });
    }

    // SCENARIO

    var scenario = function() {

        function get_run_status(callback) {
            $.get('get_run_status/', function(response) {
                var percentage = response['percentage'];
                var description = response['description'];
                callback(percentage, description);
            }, 'json').fail(
                function(e) { report_server_error('request run status', e); }
            );
        }

        function get_scenario_metadata(callback) {
            $.get('get_scenario_metadata/', function(response) {
                var scenario_name = response['name'];
                var scenario_description = response['description'];
                document.getElementById('scenario-title').innerHTML = scenario_name;
                document.getElementById('scenario-metadata-modal-name').innerHTML = scenario_name;
                document.getElementById('scenario-metadata-modal-description').innerHTML = scenario_description;
                timestep.sim_ts = response['timestep'];
                var lat = response['view']['lat'];
                var lon = response['view']['lon'];
                var zoom = response['view']['zoom'];
                var timesteps = response['timesteps']
                var timestep_selector = document.getElementById('run-timestep-selector');
                for (var i = 0; i < timesteps['steps'].length; i++) {
                    var option_element = document.createElement('option');
                    var num_steps = timesteps['steps'][i];
                    var unit_str = timesteps['unit_plural'];
                    if (num_steps == 1) {
                        unit_str = timesteps['unit_singular'];
                    }
                    option_element.text = num_steps + ' ' + unit_str;
                    timestep_selector.add(option_element);
                }
                callback(scenario_name, scenario_description, lat, lon, zoom);
                var exports_results = response['exports_results'];
                if (!exports_results) {
                    $('#export-results-btn').hide();
                }
            }, 'json').fail(
                function(e) { report_server_error('request information about the scenario', e); }
            );
        }

        function get_simulation_dates() {
            var source = document.getElementById('simulation-date-template').innerHTML;
            var template = Handlebars.compile(source);
            $.get('get_simulation_dates/', function(response) {
                var start_date = response['start']
                var end_date = response['end']
                var sd = new Date(start_date);
                var ed = new Date(end_date);
                var start_date_num = sd.getTime();
                var end_date_num = ed.getTime();
                delete sd;
                delete ed;
                var context = {start_date: start_date, end_date: end_date, start_date_num: start_date_num, end_date_num: end_date_num};
                var html = template(context);
                $('#status-div').append(html);
                $("#simulation-current-range").bootstrapSlider();
                var now = response['now'];
                set_simulation_date(now);
                toggle_scenario_buttons(now >= end_date, false, false);
            }, 'json').fail(
                function(e) { report_server_error('get_simulation_dates', e); }
            );
        }

        function set_simulation_date(current) {
            $('#simulation-current').prop('value', current);
            var now = new Date(current);
            $("#simulation-current-range").bootstrapSlider('setValue', now.getTime());
            delete now;
        }

        function toggle_scenario_buttons(disable_run, disable_reset, disable_export) {
            $('#run-scenario-btn').prop('disabled', disable_run);
            $('#reset-scenario-btn').prop('disabled', disable_reset);
            $('#export-results-btn').prop('disabled', disable_export);
        }

        function reset_scenario() {
            toggle_scenario_buttons(true, true, true);
            $.post('reset_scenario', function(response) {
                var current = response['now'];
                set_simulation_date(current);
                layer_data_dialogs.clear_layer_data_dialogs();
                map_layer_manager.clear_layers();
                model_inputs.reset_input_values();
                model_outputs.clear_outputs();
                sync_scenario_state();
            }, 'json').fail(
                function(e) { report_server_error('reset_scenario', e); }
            ).always(function() {
                toggle_scenario_buttons(false, false, false);
            });
        }

        function run_scenario() {
            progress.show(function() { get_run_status(progress.update); } );
            // Disable buttons during run
            toggle_scenario_buttons(true, true, true);
            var eos = false;
            // Get the number of timesteps to run
            var num_timesteps = parseInt(document.getElementById('run-timestep-selector').value.split(' ')[0]);
            // Get input values
            var input_values = model_inputs.get_input_values();
            var run_args = {'num_timesteps': num_timesteps, 'input_values': input_values};
            $.post('run_scenario', JSON.stringify(run_args), function(response) {
                // Get the new current simulation date
                var current = response['now'];
                set_simulation_date(current);
                // Disable run button if at end of simulation period
                var end = response['end'];
                if (current >= end) { eos = true; }
                // Get the latest scenario output values
                var output_values = response['outputs'];
                model_outputs.set_output_values(output_values);
                // Retrieve the latest layer data and render
                map_layer_manager.get_layer_data();
                // Update any layer data dialogs
                layer_data_dialogs.update_layer_data_dialogs();
            }, 'json').fail(
                function(e) { report_server_error('run_scenario', e); }
            ).always(function() {
                toggle_scenario_buttons(eos, false, false);
                progress.hide();
            });
        }

        function sync_scenario_state() {
            $.get('get_simulation_dates/', function(response) {
                set_simulation_date(response['now']);
            }, 'json').fail(
                function(e) { report_server_error('get_simulation_dates', e); }
            );
            $.get('get_all_input_data/', function(response) {
                model_inputs.set_input_values(response);
            }, 'json').fail(
                function(e) { report_server_error('get_all_input_data', e); }
            );
            map_layer_manager.get_layer_data();
            $.get('get_all_output_data/', function(response) {
                model_outputs.set_output_values(response);
            }, 'json').fail(
                function(e) { report_server_error('get_all_output_data', e); }
            );
        }

        function export_results() {
            $('#spinner-div').show();
            $.post('export_results/', function(response) {
                var filename = response['filename'];
                var type = response['type'];
                var base64 = response['data'];
                // Convert base64 encoded data string to bytes
                var raw = window.atob(base64);
                var rawLength = raw.length;
                var array = new Uint8Array(new ArrayBuffer(rawLength));
                for(var i = 0; i < rawLength; i++) {
                    array[i] = raw.charCodeAt(i);
                }
                // Insert data for export via browser
                var blob = new Blob([array], { type: type });
                var lnk = document.createElement('a');
                lnk.href = window.URL.createObjectURL(blob);
                lnk.download = filename;
                document.body.appendChild(lnk);
                lnk.click();
                document.body.removeChild(lnk);
            }, 'json').fail(
                function(e) { report_server_error('export_results', e); }
            ).always(function() {
                $('#spinner-div').hide();
            });
        }

        return {
            get_scenario_metadata: get_scenario_metadata,
            get_simulation_dates: get_simulation_dates,
            reset_scenario: reset_scenario,
            run_scenario: run_scenario,
            export_results: export_results
        }
    }();

    // MAP BASE (TILE) MANAGER

    var map_base_manager = function() {

        var map;
        var tile_options;
        var current_tile;

        function initialise_map(lat, lon, zoom) {
            this.map = L.map('map-leaflet-div').setView([lat, lon], zoom);
            L.control.scale({'position': 'topright'}).addTo(this.map);
            populate_tile_options();
        }

        function populate_tile_options() {
            tile_options = {};
            tile_options['Open Topo Map'] = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                    attribution: 'Map data: &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
                    maxZoom: 19,
                });
            tile_options['CartoDB Light'] = L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
                    subdomains: 'abcd',
                    maxZoom: 19
                });
            tile_options['CartoDB Dark'] = L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
                    subdomains: 'abcd',
                    maxZoom: 19
                });
            tile_options['ESRI World Imagery'] = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                });
            var selector = document.getElementById('map-tile-selector');
            for (var key in tile_options) {
                var opt = document.createElement('option');
                opt.text = key;
                opt.value = key;
                selector.add(opt);
            }
            $('#map-tile-selector').multiselect({
                    templates: {
                        li: '<li><a class="dropdown-item"><label class="m-0 pl-2 pr-0"></label></a></li>',
                        ul: ' <ul class="multiselect-container dropdown-menu p-1 m-0"></ul>',
                        button: '<button type="button" class="multiselect dropdown-toggle" data-toggle="dropdown" data-flip="false"></button>',
                        filter: '<li class="multiselect-item filter"><div class="input-group m-0"><input class="form-control multiselect-search" type="text"></div></li>',
                        filterClearBtn: '<span class="input-group-btn"><button class="btn btn-secondary multiselect-clear-filter" type="button"><i class="fas fa-minus-circle"></i></button></span>'
                    },
                    buttonClass: 'btn btn-secondary',
                    onChange: function(opt, checked, sel) {
                        var tile_id = $(opt).val();
                        use_tile_option(tile_id);
                    }
                });
            use_tile_option('Open Topo Map');
        }

        function use_tile_option(tile_id) {
            if (current_tile != null) {
                map_base_manager.map.removeLayer(current_tile);
            }
            current_tile = tile_options[tile_id];
            current_tile.addTo(map_base_manager.map);
        }

        return {
            initialise_map: initialise_map,
            populate_tile_options: populate_tile_options,
            map: map
        }
    }();

    // MAP LAYER MANAGER

    var map_layer_manager = function() {

        var map_click_manager = function() {

            var latlng;
            var infos = [];

            var register_map_click = function(e) {
                latlng = e.latlng;
                for (var i = 0; i < infos.length; i++) {
                    $('#layer-info-img-'+(i+1)).off('click', open_layer_data_dialog);
                }
                infos = [];
                $('#layer-info-table tr').remove();
                var header = '<tr><th class="layer-info-header-layer">Capa</th><th class="layer-info-header-cell">Celda</th>' +
                    '<th class="layer-info-header-value">Valor</th><th class="layer-info-header-data">Dato</th></tr>';
                $('#layer-info-table').append(header);
                var coordinates = 'Latitud: '+latlng['lat'].toFixed(5)+', Longitud: '+latlng['lng'].toFixed(5);
                $('#layer-info-header').text(coordinates);
            };

            var register_layer_click = function(info) {
                var layer_name = info['name'];
                var layer_cell = info['cell'];
                var layer_value = info['value'].toFixed(5);
                var id = infos.length;
                var data_icon = 'N/A';
                if (info['data']) {
                    data_icon = '<img id="layer-info-img-'+id+'" class="layer-info-img" src="static/resources/img/chart-icon.png"></img>';
                }
                var tr = '<tr><td class="layer-info-row-layer">'+layer_name+'</td><td class="layer-info-row-cell">'+layer_cell+'</td>' +
                    '<td class="layer-info-row-value">'+layer_value+'</td><td class="layer-info-row-data">'+data_icon+'</td></tr>';
                $('#layer-info-table').append(tr);
                if (info['data']) {
                    $('#layer-info-img-'+id).on('click', {id:id}, open_layer_data_dialog);
                }
                infos.push(info);
            };

            var open_layer_data_dialog = function(e) {
                var info = infos[e.data.id];
                layer_data_dialogs.spawn_layer_data_dialog(info.id, info.type, info.ident, info.title, latlng);
            };

            return {
                register_map_click: register_map_click,
                register_layer_click : register_layer_click
            };
        }();

        function initialise_layer_info_window() {
            map_base_manager.map.on('preclick', function(e) {
                map_click_manager.register_map_click(e);
            });
            var min_height = 128;
            var max_height = 200;
            var start_height = Math.min(max_height, Math.max(min_height, ((window.innerHeight - 240) * 0.25)));
            jsPanel.create({
                theme: 'primary',
                contentSize: {
                    width: function() { return Math.min(400, window.innerWidth * 0.3); },
                    height: start_height
                },
                position: 'left-bottom 10 -50',
                animateIn: 'jsPanelFadeIn',
                headerTitle: 'Informacion Capa',
                container: $('#map-div'),
                content: '<div id="layer-info-header-div"><label id="layer-info-header"></label></div><div id="layer-info-div"><table id="layer-info-table"></table></div>',
                dragit: { containment: [110, 10, 50, 10] },
                maximizedMargin: [110, 10, 50, 10],
                resizeit: { 'minWidth' : Math.min(400, window.innerWidth * 0.3),
                            'minHeight' : min_height
                          },
                headerControls: { 'close' : 'remove' }
            });
        }

        var map_layers = {};
        var stacked_map_layer_ids = [];
        var layer_vis_states = {};

        var map_layer_factory = function() {

            var layer_templates;

            function compile_layer_templates() {
                return io_common.compile_templates([
                    'layer-tooltip',
                    'layer-dropdown-template-description',
                    'layer-dropdown-template-geotiff'
                    ]);
            }

            function create_map_layer(json_layer) {
                // Common helper functions
                function build_tooltip(layer_name, metadata) {
                    var context = {name: layer_name, items: []};
                    for (var key in metadata) {
                        context['items'].push({name: key, value: metadata[key]});
                    }
                    return layer_templates['layer-tooltip'](context);
                };
                function highlight_feature(target) {
                    var oc = target.options.color;
                    var nc = charting.invert_color(oc);
                    var ns = {color: nc};
                    var ofc = target.options.fillColor;
                    if (ofc != null) {
                        var nfc = charting.invert_color(ofc);
                        ns['fillColor'] = nfc;
                    }
                    target.setStyle(ns);
                };
                if (typeof layer_templates === 'undefined') {
                    layer_templates = compile_layer_templates();
                }
                // Common
                var map_layer = {
                    id: json_layer['id'],
                    type: json_layer['type'],
                    name: json_layer['name'],
                    index: json_layer['index'],
                    display: json_layer['display'],
                    description: json_layer['description'],
                    data: null,
                    click: null,
                    map_layer: null,
                    visible: json_layer['show'],
                    pane_index: 0
                }
                if ('click' in json_layer) {
                    map_layer.click = json_layer['click'];
                }
                map_layer.set_data = function(data) {
                    this.data = data;
                    if (data == null) {
                        if (this.features) {
                            this.features = [];
                        }
                    }
                };
                map_layer.clear = function() {
                    this.data = null;
                    if (this.features) {
                        this.features = [];
                    }
                };
                map_layer.add_layer = function(map, refresh) {
                    if (refresh == undefined) {
                        refresh = true;
                    }
                    if (refresh) {
                        this.map_layer = this.build_layer();
                    }
                    if (!!this.map_layer) {
                        this.map_layer.addTo(map);
                    }
                };
                map_layer.remove_layer = function(map) {
                    if (!!this.map_layer) {
                        map.removeLayer(this.map_layer);
                    }
                };
                map_layer._create_pane = function(isMarker) {
                    if (isMarker == undefined) {
                        isMarker = false;
                    }
                    var pane_name = this.id;
                    var pane = map_base_manager.map.getPane(pane_name);
                    if (pane === undefined) {
                        pane = map_base_manager.map.createPane(pane_name);
                        var base_index = isMarker ? 600 : 400;
                        pane.style.zIndex = base_index + this.pane_index;
                    }
                };
                map_layer.append_layer_legend_element = function(parent) {
                    var template = layer_templates['layer-dropdown-template-description'];
                    var context = {text: this.description};
                    var html = template(context);
                    $(parent).append(html);
                };
                // Specialize
                var type = json_layer['type'];
                // No Features
                if (type == 'Raster') {
                    map_layer.geometry = json_layer['geometry'];
                    map_layer.build_layer = function() {
                        if (this.data === null) {
                            return null;
                        }
                        this._create_pane();
                        var this_obj = this;
                        function get_raster_geoJSON(lat, lon, rows, cols, cellsize, cellvalues, nullvalue, display) {
                            function get_shifted_point(origin, bearing, distance) {
                                var old_lat = origin[1];
                                var old_lon = origin[0];
                                old_lat = old_lat * Math.PI / 180.0;
                                old_lon = old_lon * Math.PI / 180.0;
                                var d = distance;//Distance (m)
                                var R = 6371e3;//Earth Radius (m)
                                var brng = bearing * Math.PI / 180.0;//Bearing from North (radians)
                                var new_lat = Math.asin(Math.sin(old_lat)*Math.cos(d/R)+Math.cos(old_lat)*Math.sin(d/R)*Math.cos(brng));
                                var new_lon = old_lon + Math.atan2(Math.sin(brng)*Math.sin(d/R)*Math.cos(old_lat), Math.cos(d/R)-Math.sin(old_lat)*Math.sin(new_lat));
                                new_lat = new_lat * 180.0 / Math.PI;
                                new_lon = new_lon * 180.0 / Math.PI;
                                new_lon = ((new_lon + 540.0) % 360.0) - 180.0;
                                return [new_lon, new_lat];  
                            };
                            var cells = [];
                            var cell_points = [];
                            for (var i = 0; i <= rows; i++) {
                                cell_points.push([]);
                            }
                            var p = [lon,lat];
                            for (var r = 0; r <= rows; r++) {
                                var x = [p[0],p[1]];
                                cell_points[r][0] = x;
                                for (var c = 0; c < cols; c++) {
                                    x = get_shifted_point(x, 90, cellsize);
                                    cell_points[r][c+1] = x;
                                }
                                p = get_shifted_point(p, 180, cellsize);
                            }
                            var get_cell_polygon = function(top_left, top_right, bottom_right, bottom_left, cellvalue) {
                                var polygon = [top_left, top_right, bottom_right, bottom_left, top_left];
                                var feature = {
                                    'type': 'Feature',
                                    'properties': {'value': cellvalue},
                                    'geometry': {
                                        'type': 'Polygon',
                                        'coordinates': [polygon]
                                    }
                                };
                                return feature;
                            };
                            for (var r = 0; r < rows; r++) {
                                for (var c = 0; c < cols; c++) {
                                    var cellvalue = cellvalues[r*cols+c];
                                    if (cellvalue != nullvalue) {
                                        var cell = get_cell_polygon(cell_points[r][c], cell_points[r][c+1], cell_points[r+1][c+1], cell_points[r+1][c], cellvalue);
                                        cells.push(cell);
                                    }
                                }
                            }
                            function get_color(data_value, color_map, default_color) {
                                for (var i = 0; i < color_map.length; i++) {
                                    var map_entry = color_map[i];
                                    var operator = map_entry['o'];
                                    var color = map_entry['c'];
                                    if ('v' in map_entry) {
                                        var value = map_entry['v'];
                                        switch (operator) {
                                            case '==':
                                                if (value == data_value) {
                                                    return color;
                                                }
                                                break;
                                            case '>':
                                                if (value > data_value) {
                                                    return color;
                                                }
                                                break;
                                            case '<':
                                                if (value < data_value) {
                                                    return color;
                                                }
                                                break;
                                            case '>=':
                                                if (value >= data_value) {
                                                    return color;
                                                }
                                                break;
                                            case '<=':
                                                if (value <= data_value) {
                                                    return color;
                                                }
                                                break;
                                        }
                                    }
                                    else if (operator == 'else') {
                                        return color;
                                    }
                                    else {
                                        return default_color;
                                    }
                                }
                            };
                            var mystyle = function(feature) {
                                var s = {
                                    'weight': display['weight'],
                                    'opacity': display['opacity'],
                                    'color': display['line-color'],
                                    'fillOpacity': display['fillOpacity']
                                };
                                s['fillColor'] = get_color(feature.properties.value, display['color_map'], '#000000');
                                return s;
                            }
                            var myclick = function(e) {
                                var lat_click = e.latlng.lat;
                                var lon_click = e.latlng.lng;
                                var pnpoly = function(nvert, vertx, verty, testx, testy) {
                                    // Point Inclusion in Polygon Test - W. Randolph Franklin (WRF)
                                    var c = false;
                                    for (var i = 0, j = nvert-1; i < nvert; j = i++) {
                                        if (((verty[i]>testy) != (verty[j]>testy)) && (testx < (vertx[j]-vertx[i]) * (testy-verty[i]) / (verty[j]-verty[i]) + vertx[i])) {
                                            c = !c;
                                        }
                                    }
                                    return c;
                                };
                                var row, col;
                                for (var i = 0; i < cells.length; i++) {
                                    var top_left = cells[i].geometry.coordinates[0][0];
                                    var top_right = cells[i].geometry.coordinates[0][1];
                                    var bottom_right = cells[i].geometry.coordinates[0][2];
                                    var bottom_left = cells[i].geometry.coordinates[0][3];
                                    var vertx = [top_left[0]+180.0,top_right[0]+180.0,bottom_right[0]+180.0,bottom_left[0]+180.0];
                                    var verty = [top_left[1]+180.0,top_right[1]+180.0,bottom_right[1]+180.0,bottom_left[1]+180.0];
                                    var inside = pnpoly(4, vertx, verty, lon_click+180.0, lat_click+180.0);
                                    if (inside) {
                                        row = Math.floor(i / cols);
                                        col = i % cols;
                                        break;
                                    }
                                }
                                var type = null;
                                var has_data = false;
                                if (this_obj.click !== null) {
                                    type = this_obj.click['type'];
                                    has_data = true;
                                }
                                var info = {
                                    id: this_obj.id,
                                    type: type,
                                    name: this_obj.name,
                                    cell: '['+row+','+col+']',
                                    value: e.layer.feature.properties.value,
                                    ident: {'type':'tuple','value':'('+row+','+col+')'},
                                    title: this_obj.name+' ['+row+','+col+']',
                                    data: has_data
                                };
                                map_click_manager.register_layer_click(info);
                            };
                            return L.geoJSON(cells, { style: mystyle }).on('click', myclick);
                        };
                        return get_raster_geoJSON(this.geometry['lat'], this.geometry['lon'], this.geometry['rows'], this.geometry['cols'], this.geometry['cellsize'], this.data, this.geometry['nullvalue'], this.display);
                    };
                    return map_layer;
                }
                if (type == 'GeoTIFF') {
                    map_layer.geometry = json_layer['geometry'];
                    map_layer.build_layer = function() {
                        if (this.data === null) {
                            return null;
                        }
                        this._create_pane();
                        var buffer = Base64Binary.decodeArrayBuffer(this.data['b64']);
                        var noData = this.geometry['noData'];
                        var l = new L.leafletGeotiff('', {noData: noData, pane: this.id});
                        l.setData(buffer);
                        var minMax = l.getMinMax();
                        function compute_percentages(n) {
                            var p = [];
                            for (var i = 0; i < n - 1; i++) {
                                p.push(i / (n - 1));
                            }
                            p.push(1.0);
                            return p;
                        }
                        var cs_colors = this.display['scale'];
                        var cs_percentages = compute_percentages(cs_colors.length);
                        var cs_id = this.id + '_cs';
                        plotty.addColorScale(cs_id, cs_colors, cs_percentages);
                        var dMin = minMax[0];
                        var dMax = minMax[1];
                        if (this.display['domain'] != null) {
                            var domain = this.display['domain'];
                            dMin = domain[0];
                            dMax = domain[1];
                        }
                        var renderer = new L.LeafletGeotiff.Plotty({ displayMin: dMin, displayMax: dMax, clampLow: true, clampHigh: true, colorScale: cs_id, noData: noData, opacity: this.display['opacity'] });
                        l.setRenderer(renderer);
                        var this_obj = this;
                        l.on("click", function(e) {
                            var lat = e.latlng.lat;
                            var lon = e.latlng.lng;
                            var rc = l.getRowCol(e.latlng.lat, e.latlng.lng);
                            var col = rc[1];
                            var row = rc[0];
                            var type = null;
                            var has_data = false;
                            if (this_obj.click !== null) {
                                type = this_obj.click['type'];
                                has_data = true;
                            }
                            var info = {
                                id: this_obj.id,
                                type: type,
                                name: this_obj.name,
                                cell: '['+row+','+col+']',
                                value: e.value,
                                ident: {'type':'tuple','value':'('+row+','+col+')'},
                                title: this_obj.name+' ['+row+','+col+']',
                                data: has_data
                            };
                            map_click_manager.register_layer_click(info);
                        });
                        return l;
                    };
                    map_layer.append_layer_legend_element = function(parent) {
                        var template = layer_templates['layer-dropdown-template-geotiff'];
                        var context = {min: 'MIN', max: 'MAX', text: this.description};
                        var html = template(context);
                        $(parent).append(html);
                        var canvas = $('.layer-dropdown-template-geotiff-colorband', parent)[0];
                        var ctx = canvas.getContext('2d');
                        var gradient = ctx.createLinearGradient(0,0,canvas.width,0);
                        for (var i = 0; i < this.display.scale.length; i++) {
                            var d = this.display.scale.length - 1;
                            var f = 0.0;
                            if (d > 0) {
                                f = i / d;
                            }
                            gradient.addColorStop(f, this.display.scale[i]);
                        }
                        ctx.fillStyle = gradient;
                        ctx.fillRect(0,0,canvas.width,canvas.height);
                    };
                    return map_layer;
                }
                if (type == 'Icons') {
                    map_layer.build_layer = function() {
                        if (this.data === null) {
                            return null;
                        }
                        this._create_pane(true);
                        var map_layers = [];
                        var icon_data = this.data['icons'];
                        for (var i = 0; i < icon_data.length; i++) {
                            var image_address = 'get_image/?id=' + icon_data[i]['address'];
                            var image_width = icon_data[i]['width'];
                            var image_height = icon_data[i]['height'];
                            var icon = L.icon({
                                iconUrl: image_address,
                                iconSize: [image_width, image_height],
                                iconAnchor: [Math.round(image_width/2.0), Math.round(image_height/2.0)]
                            });
                            var lat = icon_data[i]['lat'];
                            var lon = icon_data[i]['lon'];
                            var marker = L.marker([lat, lon], {icon: icon, rotationAngle:icon_data[i]['angle'], pane: this.id})
                            map_layers.push(marker);
                        }
                        return map_layers;
                    };
                    map_layer.add_layer = function(map, refresh) {
                        if (refresh == undefined) {
                            refresh = true;
                        }
                        if (refresh) {
                            this.map_layer = this.build_layer();
                        }
                        if (!!this.map_layer) {
                            for (var i = 0; i < this.map_layer.length; i++) {
                                this.map_layer[i].addTo(map);
                            }
                        }
                    };
                    map_layer.remove_layer = function(map) {
                        if (!!this.map_layer) {
                            for (var i = 0; i < this.map_layer.length; i++) {
                                map.removeLayer(this.map_layer[i]);
                            }
                        }
                    };
                    return map_layer;
                }
                // Features
                map_layer.features = [];
                if (type == 'Points') {
                    map_layer.build_layer = function() {
                        if (this.data === null) {
                            return null;
                        }
                        this._create_pane();
                        var points = [];
                        for (var i = 0; i < this.data['points'].length; i++) {
                            var feature = {
                                'type': 'Feature',
                                'properties': {'value': this.data['metadata'][i], 'layer_id': this.id},
                                'geometry': {
                                    'type': 'Point',
                                    'coordinates': [this.data['points'][i]['lon'],this.data['points'][i]['lat']]
                                },
                                'id': i
                            };
                            points.push(feature);
                        }
                        var marker_options = {
                            radius: this.display['radius'],
                            weight: this.display['weight'],
                            opacity: this.display['opacity'],
                            fillOpacity: this.display['fillOpacity'],
                            color: this.display['color'],
                            fillColor: this.display['fillColor'],
                        };
                        var pointtooltip = function(layer) {
                            return layer.feature.properties.value.toString();
                        }
                        this.features = [];
                        var add_feature = function(this_obj, feature, layer) {
                            var point = layer.feature.geometry.coordinates;
                            this_obj.features.push({'name': feature.properties.value, 'point': point, 'bounds': null});
                        }
                        var this_obj = this;
                        var onEachFeature = function(feature, layer) {
                            add_feature(this_obj, feature, layer);
                            if (this_obj.click != null) {
                                var layer_id = feature.properties.layer_id;
                                var feature_prop = feature.properties[this_obj.click['ident']];
                                layer.on('click', function(e) {
                                    var type = this_obj.click['type'];
                                    var ident = {'type':'string','value':feature_prop};
                                    var title = feature_prop;
                                    layer_data_dialogs.spawn_layer_data_dialog(this_obj.id, type, ident, title, e.latlng);
                                });
                            }
                            layer.on('mouseover', function(e) {
                                highlight_feature(e.target);
                            });
                            layer.on('mouseout', function(e) {
                                highlight_feature(e.target);
                            });
                        }
                        return L.geoJSON(points, { onEachFeature: onEachFeature, pointToLayer: function(feature, latlng) { return L.circleMarker(latlng, marker_options); pane: this.id } }).bindTooltip(pointtooltip);        
                    };
                    return map_layer;
                }
                if (type == 'Lines') {
                    map_layer.build_layer = function() {
                        if (this.data === null) {
                            return null;
                        }
                        this._create_pane();
                        var lines = [];
                        var display_lookup = {};
                        for (var i = 0; i < this.data['lines'].length; i++) {
                            var line = [];
                            for (var j = 0; j < this.data['lines'][i].length; j++) {
                                line.push([this.data['lines'][i][j]['lon'], this.data['lines'][i][j]['lat']]);
                            }
                            var feature = {
                                'type': 'Feature',
                                'properties': {'value': this.data['metadata'][i], 'dk': i},
                                'geometry': {
                                    'type': 'LineString',
                                    'coordinates': line
                                },
                                'id': i
                            };
                            lines.push(feature);
                            if (this.display.length == this.data['lines'].length) {
                                display_lookup[i] = this.display[i];
                            }
                            else {
                                display_lookup[i] = this.display[0];
                            }
                        }
                        var linestyle = function(feature) {
                            var key = feature.properties.dk;
                            var s = {
                                'weight' : display_lookup[key]['weight'],
                                'opacity' : display_lookup[key]['opacity'],
                                'color' : display_lookup[key]['line-color']
                            };
                            return s;
                        }
                        var linetooltip = function(layer) {
                            return layer.feature.properties.value.toString();
                        }
                        this.features = [];
                        var add_feature = function(this_obj, feature, layer) {
                            var bounds = layer.getBounds();
                            this_obj.features.push({'name': feature.properties.value, 'point': null, 'bounds': bounds});
                        }
                        var this_obj = this;
                        var onEachFeature = function(feature, layer) {
                            add_feature(this_obj, feature, layer);
                            if (this_obj.click != null) {
                                var layer_id = feature.properties.layer_id;
                                var feature_prop = feature.properties[this_obj.click['ident']];
                                layer.on('click', function(e) {
                                    var type = this_obj.click['type'];
                                    var ident = {'type':'string','value':feature_prop};
                                    var title = feature_prop;
                                    layer_data_dialogs.spawn_layer_data_dialog(this_obj.id, type, ident, title, e.latlng);
                                });
                            }
                            layer.on('mouseover', function(e) {
                                highlight_feature(e.target);
                            });
                            layer.on('mouseout', function(e) {
                                highlight_feature(e.target);
                            });
                        }
                        return L.geoJSON(lines, { onEachFeature: onEachFeature, style: linestyle, pane: this.id }).bindTooltip(linetooltip);
                    };
                    return map_layer;
                }
                if (type == 'Polygons') {
                    map_layer.build_layer = function() {
                        if (this.data === null) {
                            return null;
                        }
                        this._create_pane();
                        var polygons = [];
                        var display_lookup = {};
                        for (var i = 0; i < this.data['polygons'].length; i++) {
                            var polygon = [];
                            for (var j = 0; j < this.data['polygons'][i].length; j++) {
                                polygon.push([this.data['polygons'][i][j]['lon'], this.data['polygons'][i][j]['lat']]);
                            }
                            var feature = {
                                'type': 'Feature',
                                'properties': {'value': this.data['metadata'][i], 'dk': i},
                                'geometry': {
                                    'type': 'Polygon',
                                    'coordinates': [polygon]
                                },
                                'id': i
                            };
                            polygons.push(feature);
                            if (this.display.length == this.data['polygons'].length) {
                                display_lookup[i] = this.display[i];
                            }
                            else {
                                display_lookup[i] = this.display[0];
                            }
                        }
                        var polygonstyle = function(feature) {
                            var key = feature.properties.dk;
                            var s = {
                                'weight' : display_lookup[key]['weight'],
                                'opacity' : display_lookup[key]['opacity'],
                                'fillOpacity' : display_lookup[key]['fillOpacity'],
                                'color' : display_lookup[key]['line-color'],
                                'fillColor' : display_lookup[key]['fill-color']
                            };
                            return s;
                        }
                        var polygontooltip = function(layer) {
                            return layer.feature.properties.value.toString();
                        }
                        this.features = [];
                        var add_feature = function(this_obj, feature, layer) {
                            var bounds = layer.getBounds();
                            this_obj.features.push({'name': feature.properties.value, 'point': null, 'bounds': bounds});
                        }
                        var this_obj = this;
                        var onEachFeature = function(feature, layer) {
                            add_feature(this_obj, feature, layer);
                            if (this_obj.click != null) {
                                var layer_id = feature.properties.layer_id;
                                var feature_prop = feature.properties[this_obj.click['ident']];
                                layer.on('click', function(e) {
                                    var type = this_obj.click['type'];
                                    var ident = {'type':'string','value':feature_prop};
                                    var title = feature_prop;
                                    layer_data_dialogs.spawn_layer_data_dialog(this_obj.id, type, ident, title, e.latlng);
                                });
                            }
                            layer.on('mouseover', function(e) {
                                highlight_feature(e.target);
                            });
                            layer.on('mouseout', function(e) {
                                highlight_feature(e.target);
                            });
                        }
                        return L.geoJSON(polygons, { onEachFeature: onEachFeature, style: polygonstyle, pane: this.id }).bindTooltip(polygontooltip);
                    };
                    return map_layer;
                }
                if (type == 'Shapefile') {
                    map_layer.build_layer = function() {
                        if (this.data === null) {
                            return null;
                        }
                        var this_obj = this;
                        var points_only = true;
                        for (var i = 0; i < this.data['features'].length; i++) {
                            this.data['features'][i]['properties']['LEAFLET_TOOLTIP_VALUE'] = build_tooltip(this.name, this.data['metadata'][i]);
                            this.data['features'][i]['properties']['LEAFLET_FEATURE_NAME'] = this.data['ids'][i];
                            if (this.data['features'][i]['geometry']['type'].indexOf('Point') < 0) {
                                points_only = false;
                            }
                        }
                        var features = this.data['features'];
                        var default_displays = this.display['default'];
                        var custom_displays = this.display['custom']['custom_displays'];
                        var featurekey = this.display['custom']['featurekey'];
                        var featurestyle = function(feature) {
                            if (featurekey in feature.properties) {
                                var key = feature.properties[featurekey];
                                if (key in custom_displays) {
                                    return custom_displays[key];
                                }
                            }
                            var type = feature.geometry.type;
                            if (type.indexOf('Point') >= 0) {
                                return default_displays['point'];
                            } else if (type.indexOf('Line') >= 0) {
                                return default_displays['line'];
                            } else if (type.indexOf('Polygon') >= 0) {
                                return default_displays['polygon'];
                            }
                        }
                        var pointfeaturetolayer = function(feature, latlng) {
                            var marker_options = default_displays['point'];
                            if (featurekey in feature.properties) {
                                var key = feature.properties[featurekey];
                                if (key in custom_displays) {
                                    marker_options = custom_displays[key];
                                }
                            }
                            marker_options['pane'] = this_obj.id;
                            return L.circleMarker(latlng, marker_options);
                        }
                        var featuretooltip = function(layer) {
                            return layer.feature.properties['LEAFLET_TOOLTIP_VALUE'].toString();
                        }
                        this.features = [];
                        var add_feature = function(this_obj, feature, layer) {
                            var bounds = null;
                            var point = null;
                            if (layer.feature.geometry.type === 'Point') {
                                point = layer.feature.geometry.coordinates;
                            }
                            else {
                                bounds = layer.getBounds();
                            }
                            this_obj.features.push({'name': feature.properties.LEAFLET_FEATURE_NAME.toString(), 'bounds': bounds, 'point': point});
                        }
                        var this_obj = this;
                        var onEachFeature = function(feature, layer) {
                            add_feature(this_obj, feature, layer);
                            if (this_obj.click != null) {
                                var layer_id = feature.properties.layer_id;
                                var feature_prop = feature.properties[this_obj.click['ident']];
                                layer.on('click', function(e) {
                                    var type = this_obj.click['type'];
                                    var ident = {'type':'string','value':feature_prop};
                                    var title = feature_prop;
                                    layer_data_dialogs.spawn_layer_data_dialog(this_obj.id, type, ident, title, e.latlng);
                                });
                            }
                            layer.on('mouseover', function(e) {
                                highlight_feature(e.target);
                            });
                            layer.on('mouseout', function(e) {
                                highlight_feature(e.target);
                            });
                        }
                        if (points_only) {
                            this._create_pane();
                            return L.geoJSON(features, { pointToLayer: pointfeaturetolayer, onEachFeature: onEachFeature, pane: this.id }).bindTooltip(featuretooltip);
                        }
                        else {
                            this._create_pane();
                            return L.geoJSON(features, { style: featurestyle, pointToLayer: pointfeaturetolayer, onEachFeature: onEachFeature, pane: this.id }).bindTooltip(featuretooltip);
                        }
                    };
                    return map_layer;
                }
                throw ('Layer type "' + type + '" not recognised.');
            }

            return {
                create_map_layer: create_map_layer
            }
        }();

        function initialise_layers() {
            $.get('get_layers/', function(response) {
                var selector = document.getElementById('layer-selector');
                response.sort(function(a,b) { if (a.index > b.index) { return 1; } else if (a.index < b.index) { return -1; } else { return 0; } });
                for (var i = 0; i < response.length; i++) {
                    var map_layer = map_layer_factory.create_map_layer(response[i]);
                    // NB: Are using Groups as a way of achieving the expand/collapse to show layer metadata
                    var optgroup = document.createElement('optgroup');
                    optgroup.label = map_layer.name;
                    optgroup.value = map_layer.id;
                    optgroup.selected = map_layer.visible;
                    var opt = document.createElement('option');
                    opt.text = map_layer.name;
                    opt.value = map_layer.id;
                    opt.selected = map_layer.visible;
                    optgroup.appendChild(opt);
                    selector.add(optgroup);
                    register_map_layer(map_layer);
                }
                compute_map_pane_indexes();
                $('#layer-selector').multiselect({
                    templates: {
                        li: '<li><a class="dropdown-item"><label class="m-0 pl-2 pr-0"></label></a></li>',
                        ul: ' <ul class="multiselect-container dropdown-menu p-1 m-0"></ul>',
                        button: '<button type="button" class="multiselect dropdown-toggle" data-toggle="dropdown" data-flip="false"><span class="multiselect-selected-text"></span> <b class="caret"></b></button>',
                        filter: '<li class="multiselect-item filter"><div class="input-group m-0"><input class="form-control multiselect-search" type="text"></div></li>',
                        filterClearBtn: '<span class="input-group-btn"><button class="btn btn-secondary multiselect-clear-filter" type="button"><i class="fas fa-minus-circle"></i></button></span>',
                    },
                    buttonClass: 'btn btn-secondary',
                    onChange: function(opt, checked, sel) {
                        var layer_id = $(opt[0]).val();
                        map_layers[layer_id].visible = checked;
                        render_layers(false);
                    },
                    buttonWidth: '176px',
                    maxHeight: $(window).height() * 0.8,
                    numberDisplayed: 0,
                    buttonText: function(options, select) {
                        return 'Capas de mapa';
                    },
                    enableClickableOptGroups: true,
                    enableCollapsibleOptGroups: true,
                    buttonContainer: '<div id="layer-selector-container" />'
                });
                // Fix the width of the dropdown section (to accom custom elements below)
                $('#layer-selector-container .multiselect-container').css('width', '313px');
                // Collapse all group items
                $('#layer-selector-container .caret-container').click();
                // Swap to custom caret class
                var group_items = $('#layer-selector-container .multiselect-group');
                for (var i = 0; i < group_items.length; i++) {
                    var gi = group_items[i];
                    var b = $('.caret', gi).first();
                    b.attr('class','map-layer-caret');
                }
                // Substitute in custom drop-down item elements for map layers
                var layer_items = $('#layer-selector-container .dropdown-item');
                for (var i = 0; i < layer_items.length; i++) {
                    var ddi = layer_items[i];
                    var layer_id = $('input', ddi)[0].value;
                    // Hide the standard drop-down item element
                    var standard_element = ddi.childNodes[0];
                    standard_element.setAttribute('hidden','hidden');
                    // Add our own drop-down item element based on map layer instance
                    var ml = map_layers[layer_id];
                    ml.append_layer_legend_element(ddi);
                }
                get_layer_data();
            }, 'json').fail(
                function(e) { report_server_error('get_layers', e); }
            );
            initialise_layer_info_window();
        }

        function register_map_layer(map_layer) {
            map_layers[map_layer.id] = map_layer;
        }

        function calculate_ordered_ids() {
            var indexes = [];
            for (var id in map_layers) {
                indexes.push(map_layers[id].index);
            }
            indexes.sort();
            var ordered_ids = [];
            for (var i in indexes) {
                for (var id in map_layers) {
                    if (map_layers[id].index == i) {
                        ordered_ids.push(id);
                    }
                }
            }
            return ordered_ids;
        }

        function compute_map_pane_indexes() {
            stacked_map_layer_ids = calculate_ordered_ids();
            var pane_index = 1;
            for (var i = 0; i < stacked_map_layer_ids.length; i++) {
                var id = stacked_map_layer_ids[i];
                map_layers[id].pane_index = pane_index;
                pane_index = pane_index + 1;
            }
        }

        function get_layer_data() {
            $.get('get_all_layer_data/', function(response) {
                for (var id in response) {
                    var map_layer = map_layers[id];
                    map_layer.set_data(response[id]);
                }
                render_layers(true);
            }, 'json').fail(
                function(e) { report_server_error('get_all_layer_data', e); }
            );
        }

        function create_state_cache() {
            var states = {};
            for (var id in map_layers) {
                states[id] = map_layers[id].visible;
            }
            return states;
        }

        function render_layers(refresh_data) {
            if (refresh_data) {
                clear_layers();
            }
            var ordered_ids = stacked_map_layer_ids;
            var visible_layers = [];
            for (var i = 0; i < ordered_ids.length; i++) {
                var id = ordered_ids[i];
                var map_layer = map_layers[id];
                if (map_layer.visible) {
                    visible_layers.push(map_layer);
                    if (refresh_data) {
                        map_layer.add_layer(map_base_manager.map);
                    }
                }
            }
            if (refresh_data) {
                layer_vis_states = create_state_cache();
            }
            else {
                var updated_layer_vis_states = create_state_cache();
                for (var i in ordered_ids) {
                    var id = ordered_ids[i];
                    if (updated_layer_vis_states[id] !== layer_vis_states[id]) {
                        if (updated_layer_vis_states[id]) {
                            map_layers[id].add_layer(map_base_manager.map);
                        } else {
                            map_layers[id].remove_layer(map_base_manager.map);
                        }
                        break;
                    }
                }
                layer_vis_states = updated_layer_vis_states;
            }
            feature_finder.update_features(visible_layers);
            feature_finder.refresh_feature_finder();
        }

        function clear_layers() {
            for (var id in map_layers) {
                var map_layer = map_layers[id];
                map_layer.remove_layer(map_base_manager.map);
            }
        }

        function highlight_feature(layer_id, feature_index) {

            const BLINK_INTERVAL = 800;
            const BLINK_TIMEOUT = 5000;

            var feature_blink = function(f) {
                var timer_id = setInterval(function() {
                    var oc = f.options.color;
                    var nc = charting.invert_color(oc);
                    var ns = {color: nc};
                    var ofc = f.options.fillColor;
                    if (ofc != null) {
                        var nfc = charting.invert_color(ofc);
                        ns['fillColor'] = nfc;
                    }
                    f.setStyle(ns);
                }, BLINK_INTERVAL);
                setTimeout(function() {
                    clearInterval(timer_id);
                }, BLINK_TIMEOUT);
            };
            map_layers[layer_id].map_layer.eachLayer(function (f) {
                if (f.feature.id == feature_index) {
                    feature_blink(f);
                }
            });
        }

        return {
            initialise_layers: initialise_layers,
            get_layer_data: get_layer_data,
            clear_layers: clear_layers,
            highlight_feature: highlight_feature
        }
    }();

    // INPUTS

    var model_inputs = function() {

        var input_views = {};

        var model_inputs_view_factory = function() {

            var input_templates;

            function compile_input_templates() {
                return io_common.compile_templates([
                    'input-template-numeric',
                    'input-template-bound-numeric',
                    'input-template-boolean',
                    'input-template-single-selection',
                    'input-template-multi-selection'
                    ]);
            }

            function create_input_view(json_input) {
                if (typeof input_templates === 'undefined') {
                    input_templates = compile_input_templates();
                }
                // Common
                var input_view = {
                    id: json_input['id'],
                    type: json_input['type'],
                    name: json_input['name'],
                    def: json_input['default'],
                    data: json_input['default'],
                    group: json_input['group'],
                    subgroup: json_input['subgroup']
                }
                input_view.get_value = function() {
                    return this.data;
                };
                input_view.set_value = function(value) {
                    this.set_value_internal(value);
                    this.refresh_control();
                };
                input_view.clear = function() {
                    this.data = this.def;
                };
                input_view.set_value_internal = function(value) {
                    this.data = value;
                };
                input_view.hookup_events = function() {}
                // Specialize
                var type = json_input['type'];
                if (type === 'Numeric') {
                    input_view.step = json_input['step'];
                    input_view.positive = json_input['positive'];
                    input_view.zero = json_input['zero'];
                    input_view.negative = json_input['negative'];
                    input_view.generate_html = function() {
                        var template = input_templates['input-template-numeric'];
                        var set_min = false;
                        var set_max = false;
                        var min, max;
                        if (!input_view.positive) {
                            set_max = true;
                            if (input_view.zero) { max = 0; } else { max = 0 - Number.MIN_VALUE; }
                        }
                        else if (!input_view.negative) {
                            set_min = true;
                            if (input_view.zero) { min = 0; } else { min = Number.MIN_VALUE; }
                        }
                        var title = 'Valor debe ser' + ' ';
                        if (input_view.positive) { title += 'positivo' + ', '; }
                        if (input_view.negative) { title += 'negativo' + ', '; }
                        if (!input_view.zero) { title += 'pero no' + ' '; }
                        else { title += 'o' + ' '; }
                        title += 'cero y un multiplo de' + ' ' + input_view.step;
                        var context = {name: this.name, set_min: set_min, min: min, set_max: set_max, max: max, step: this.step, title: title, id: this.id};
                        return template(context);
                    };
                    input_view.refresh_control = function() {
                        $('#input-template-numeric-'+this.id).prop('value', this.data);
                    };
                    input_view.hookup_events = function() {
                        var this_ref = this;
                        $('#input-template-numeric-'+this.id).on('change', function(event_obj) {
                            var val = parseFloat(event_obj.target.value);
                            if (isNaN(val)) {
                                $('#input-template-numeric-'+this_ref.id).css('borderColor', 'red');
                                $('#input-template-numeric-'+this_ref.id).css('borderWidth', '3px');
                            } else {
                                $('#input-template-numeric-'+this_ref.id).css('borderColor', 'black');
                                $('#input-template-numeric-'+this_ref.id).css('borderWidth', '1px');
                                this_ref.set_value_internal(val);
                            }
                        });
                    };
                    return input_view;
                }
                if (type === 'BoundNumeric') {
                    input_view.min = json_input['min'];
                    input_view.max = json_input['max'];
                    input_view.step = json_input['step'];
                    input_view.generate_html = function() {
                        var template = input_templates['input-template-bound-numeric'];
                        var context = {name: this.name, min: this.min, max: this.max, step: this.step, def: this.def, id: this.id};
                        return template(context);
                    };
                    input_view.refresh_control = function() {
                        $('#input-template-bound-numeric-slider-'+this.id).bootstrapSlider('setValue', this.data);
                        $('#input-template-bound-numeric-preview-'+this.id).prop('value', this.data);
                    };
                    input_view.hookup_events = function() {
                        var this_ref = this;
                        $('#input-template-bound-numeric-slider-'+this.id).bootstrapSlider();
                        $('#input-template-bound-numeric-slider-'+this.id).on('slide', function(event_obj) {
                            this_ref.set_value_internal(parseFloat(event_obj.value));
                        });
                        $('#input-template-bound-numeric-slider-'+this.id).on('input', function(event_obj) {
                            $('#input-template-bound-numeric-preview-'+this_ref.id).prop('value', event_obj.target.value);
                        });
                        // change event for IE
                        $('#input-template-bound-numeric-slider-'+this.id).on('change', function(event_obj) {
                            $('#input-template-bound-numeric-preview-'+this_ref.id).prop('value', event_obj.target.value);
                        });
                    };
                    return input_view;
                }
                if (type === 'Boolean') {
                    input_view.generate_html = function() {
                        var template = input_templates['input-template-boolean']
                        var context = {name: this.name, def: this.def, id: this.id};
                        return template(context);
                    };
                    input_view.refresh_control = function() {
                        $('#input-template-boolean-checkbox-'+this.id).bootstrapSwitch('state', this.data, false);
                    };
                    input_view.hookup_events = function() {
                        var this_ref = this;
                        $('#input-template-boolean-checkbox-'+this.id).attr('data-on-text', 'Sí');
                        $('#input-template-boolean-checkbox-'+this.id).attr('data-off-text', 'No');
                        $('#input-template-boolean-checkbox-'+this.id).bootstrapSwitch();
                        $('#input-template-boolean-checkbox-'+this.id).on('switchChange.bootstrapSwitch', function(event_obj, state) {
                            this_ref.set_value_internal(state);
                        });
                    };
                    return input_view;
                }
                if (type === 'SingleSelection') {
                    input_view.options = json_input['options'];
                    if (input_view.def == undefined) {
                        var first = input_view.options[0];
                        input_view.def = first;
                        input_view.data = first;
                    }
                    input_view.generate_html = function() {
                        var template = input_templates['input-template-single-selection'];
                        var template_options = [];
                        for (var i = 0; i < this.options.length; i++) {
                            var name = this.options[i];
                            var ticked = false;
                            if (name == this.def) {
                                ticked = true;
                            }
                            template_options.push({ 'name' : name, 'ticked' : ticked });
                        }
                        var context = {name: this.name, options: template_options, id: this.id};
                        return template(context);
                    };
                    input_view.refresh_control = function() {
                        $('#input-template-single-selection-select-'+this.id).val(this.data);
                    };
                    input_view.hookup_events = function() {
                        var this_ref = this;
                        $('#input-template-single-selection-select-'+this.id).on('change', function(event_obj) {
                            this_ref.set_value_internal(event_obj.target.value);
                        });
                    };
                    return input_view;
                }
                if (type === 'MultiSelection') {
                    input_view.options = json_input['options'];
                    input_view.data = {};
                    for (var i = 0; i < input_view.options.length; i++) {
                        var name = input_view.options[i];
                        var ticked = false;
                        if (input_view.def.indexOf(name) >= 0) {
                            ticked = true;
                        }
                        input_view.data[name] = ticked;
                    }
                    input_view.def = input_view.data;
                    input_view.generate_html = function() {
                        var template = input_templates['input-template-multi-selection'];
                        var template_options = [];
                        for (var i = 0; i < this.options.length; i++) {
                            var name = this.options[i];
                            var ticked = false;
                            if (name in this.def) {
                                ticked = this.def[name];
                            }
                            template_options.push({ 'name' : name, 'ticked' : ticked });
                        }
                        var context = {name: this.name, options: template_options, id: this.id};
                        return template(context);
                    };
                    input_view.get_value = function() {
                        var selected = [];
                        for (var key in this.data) {
                            if (this.data[key]) {
                                selected.push(key);
                            }
                        }
                        return selected;
                    };
                    input_view.set_value = function(selected) {
                        for (var i = 0; i < this.options.length; i++) {
                            var name = this.options[i];
                            var ticked = false;
                            if (selected.indexOf(name) >= 0) {
                                ticked = true;
                            }
                            this.data[name] = ticked;
                        }
                        this.refresh_control();
                    };
                    input_view.refresh_control = function() {
                        for (var key in this.data) {
                            var action = (this.data[key]) ? 'select' : 'deselect';
                            $('#input-template-multi-selection-dropdown-'+this.id).multiselect(action, key);
                        }
                    };
                    input_view.set_value_internal = function(opt, checked) {
                        this.data[opt] = checked;
                    };
                    input_view.hookup_events = function() {
                        var this_ref = this;
                        // Hack from GitHub issue comment to get bootstrap-multiselect working in BS4-beta
                        $('#input-template-multi-selection-dropdown-'+this.id).multiselect({
                            templates: {
                                li: '<li><a class="dropdown-item"><label class="m-0 pl-2 pr-0"></label></a></li>',
                                ul: ' <ul class="multiselect-container dropdown-menu p-1 m-0"></ul>',
                                button: '<button type="button" class="multiselect dropdown-toggle" data-toggle="dropdown" data-flip="false"><span class="multiselect-selected-text"></span> <b class="caret"></b></button>',
                                filter: '<li class="multiselect-item filter"><div class="input-group m-0"><input class="form-control multiselect-search" type="text"></div></li>',
                                filterClearBtn: '<span class="input-group-btn"><button class="btn btn-secondary multiselect-clear-filter" type="button"><i class="fas fa-minus-circle"></i></button></span>'
                            },
                            //buttonContainer: '<div class="dropdown" />',
                            buttonClass: 'btn btn-secondary',
                            onChange: function(opt, checked, sel) {
                                this_ref.set_value_internal($(opt).val(), checked);
                            }
                        });
                    };
                    return input_view;
                }
                throw ('Input type "' + type + '" not recognised.');
            }

            return {
                create_input_view: create_input_view
            }
        }();

        function initialise_inputs() {
            var spacing = 45;
            var layer_info_window_size = Math.min(200, Math.max(128, ((window.innerHeight - 240) * 0.25)));
            var content_height = ((window.innerHeight - 240) - layer_info_window_size - spacing);
            jsPanel.create({
                theme: 'primary',
                contentSize: {
                    width: function() { return Math.min(400, window.innerWidth * 0.3); },
                    height: content_height
                },
                position: 'left-top 10 110',
                animateIn: 'jsPanelFadeIn',
                headerTitle: 'Entradas',
                container: $('#map-div'),
                content: '<div id="inputs-div"></div>',
                dragit: { containment: [110, 10, 50, 10] },
                maximizedMargin: [110, 10, 50, 10],
                headerControls: { 'close' : 'remove' }
            });
            $.get('get_inputs/', function(response) {
                var input_tab_template = io_common.compile_templates(['input-template-tabs'])['input-template-tabs'];
                io_common.get_variables(response, 'input', input_tab_template,
                model_inputs_view_factory.create_input_view, register_input_view, set_input_values, false);
            }, 'json').fail(
                function(e) { report_server_error('get_inputs', e); }
            );
        }

        function register_input_view(input_view) {
            input_views[input_view.id] = input_view;
        }

        function get_input_values() {
            var input_values = {};
            for (var id in input_views) {
                input_values[id] = input_views[id].get_value();
            }
            return input_values;
        }

        function set_input_values(input_values) {
            for (var id in input_values) {
                input_views[id].set_value(input_values[id]);
            }
        }

        function reset_input_values() {
            for (var i = 0; i < input_views.length; i++) {
                input_views[i].clear();
            }
        }

        return {
            initialise_inputs: initialise_inputs,
            get_input_values: get_input_values,
            set_input_values: set_input_values,
            reset_input_values: reset_input_values
        }
    }();

    // OUTPUTS

    var model_outputs = function() {

        var output_views = {};

        var model_outputs_view_factory = function() {

            var output_templates;

            function compile_output_templates() {
                return io_common.compile_templates([
                    'output-template-default',
                    'output-template-value',
                    'output-template-radar',
                    'output-template-gauge',
                    'output-template-image'
                    ]);
            }

            function create_output_view(json_output) {
                // Common helper functions
                function build_default_template(view_obj) {
                    var template = output_templates['output-template-default'];
                    var context = {name: view_obj.name, id: view_obj.id, type: view_obj.ELEMENT_TYPE};
                    return template(context);
                }
                function refresh_chart_control(view_obj, cfg) {
                    if (view_obj.tab_hidden || view_obj.container_hidden) { return; }
                    var ctx = document.getElementById('output-template-'+view_obj.ELEMENT_TYPE+'-graph-'+view_obj.id).getContext("2d");
                    if (view_obj.chart != null) { view_obj.chart.destroy(); }
                    view_obj.chart = new Chart(ctx, cfg);
                }
                function hookup_export_data_event(view_obj) {
                    $('#output-template-'+view_obj.ELEMENT_TYPE+'-export-img-'+view_obj.id).on('click', function(e) {
                        export_data.send_to_clipboard(view_obj, origin='OUTPUT');
                    });
                }
                if (typeof output_templates === 'undefined') {
                    output_templates = compile_output_templates();
                }
                // Common
                var output_view = { 
                    id: json_output['id'],
                    type: json_output['type'],
                    name: json_output['name'],
                    data: null,
                    display: json_output['display'],
                    group: json_output['group'],
                    tab_hidden: false,
                    container_hidden: false
                };
                output_view.hookup_events = function() {}
                output_view.set_value = function(value) {
                    this.data = value;
                    this.refresh_control();
                };
                output_view.clear = function() {
                    this.data = null;
                    this.refresh_control();
                };
                output_view.tab_hide = function() {};
                output_view.tab_show = function() {};
                output_view.container_hide = function() {};
                output_view.container_show = function() {};
                // Specialize
                var type = json_output['type'];
                // No Chart
                if (type === 'Numeric') {
                    output_view.ELEMENT_TYPE = 'value';
                    var decimal_places = output_view.display['decimal-places'];
                    output_view.generate_html = function() {
                        return output_templates['output-template-'+this.ELEMENT_TYPE]({name: this.name, id: this.id});
                    };
                    output_view.refresh_control = function() {
                        var value = this.data;
                        if (decimal_places >= 0 && value != null) {
                            value = parseFloat(value).toFixed(decimal_places);
                        }
                        $('#output-template-'+this.ELEMENT_TYPE+'-value-'+this.id).prop(this.ELEMENT_TYPE, value);
                    };
                    output_view.hookup_events = function() {
                        hookup_export_data_event(this, this.ELEMENT_TYPE);
                    };
                    return output_view;
                }
                if (type === 'Image') {
                    output_view.ELEMENT_TYPE = 'image';
                    output_view.generate_html = function() {
                        return output_templates['output-template-'+this.ELEMENT_TYPE]({name: this.name, id: this.id});
                    };
                    output_view.refresh_control = function() {
                        var ident = this.data;
                        if (ident != null) {
                            var image_address = 'get_image/?id=' + ident;
                            $('#output-template-'+this.ELEMENT_TYPE+'-image-'+this.id).prop('src', image_address);
                        } else {
                            $('#output-template-'+this.ELEMENT_TYPE+'-image-'+this.id).prop('src', '');
                        }
                    };
                    output_view.hookup_events = function() {
                        var ov = this;
                        $('#output-template-'+this.ELEMENT_TYPE+'-export-img-'+this.id).on('click', function(e) {
                            export_data.save_to_disk(ov, origin='OUTPUT');
                        });
                    };
                    return output_view;
                }
                // Hide / Show
                output_view.tab_hide = function() {
                    this.tab_hidden = true;
                };
                output_view.tab_show = function() {
                    this.tab_hidden = false;
                    this.refresh_control();
                };
                output_view.container_hide = function() { 
                    this.container_hidden = true;
                    if (this.chart != null) {
                        this.chart.destroy();
                        this.chart = null;
                    }
                };
                output_view.container_show = function() {
                    this.container_hidden = false;
                    this.refresh_control();
                };
                if (type === 'Gauge') {
                    output_view.ELEMENT_TYPE = 'gauge';
                    output_view.min = json_output['min'];
                    output_view.max = json_output['max'];
                    output_view.gauge = null;
                    output_view.generate_html = function() {
                        return output_templates['output-template-'+this.ELEMENT_TYPE]({name: this.name, id: this.id});
                    };
                    output_view.refresh_control = function() {
                        if (this.tab_hidden || this.container_hidden) { return; }
                        var el_id = 'output-template-'+this.ELEMENT_TYPE+'-graph-'+this.id;
                        if (this.gauge === null) {
                            var ctx = document.getElementById(el_id);
                            var cfg = charting.gauge(this.min, this.max, this.display);
                            this.gauge = new Gauge(ctx).setOptions(cfg);
                            this.gauge.maxValue = this.max;
                            this.gauge.setMinValue(this.min);
                            this.gauge.animationSpeed = 4;
                            $('#'+el_id).tooltip();
                        }
                        $('#'+el_id).attr('data-original-title', this.data);
                        this.gauge.set(this.data);
                    };
                    output_view.hookup_events = function() {
                        hookup_export_data_event(this);
                    };
                    return output_view;
                }
                // Chart
                output_view.data = [];
                output_view.chart = null;
                output_view.clear = function() {
                    this.data = [];
                    this.refresh_control();
                };
                if (type === 'TimeSeries') {
                    output_view.ELEMENT_TYPE = 'timeseries';
                    output_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    output_view.refresh_control = function() {
                        refresh_chart_control(this, charting.timeseries(this.data, this.display));
                    };
                    output_view.hookup_events = function() {
                        var this_obj = this;
                        charting.attach_click_event_handler('output-template-'+this.ELEMENT_TYPE+'-graph-'+this.id, function(e) { this_obj.chart.resetZoom(); });
                        hookup_export_data_event(this);
                    };
                    return output_view;
                }
                if (type === 'TimeSeriesWithIntervals') {
                    output_view.ELEMENT_TYPE = 'timeseries';
                    output_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    output_view.refresh_control = function() {
                        refresh_chart_control(this, charting.timeseries_with_intervals(this.data, this.display));
                    };
                    output_view.hookup_events = function() {
                        var this_obj = this;
                        charting.attach_click_event_handler('output-template-'+this.ELEMENT_TYPE+'-graph-'+this.id, function(e) { this_obj.chart.resetZoom(); });
                        hookup_export_data_event(this);
                    };
                    return output_view;
                }
                if (type === 'Radar') {
                    output_view.ELEMENT_TYPE = 'radar';
                    output_view.variables = json_output['variables'];
                    var filter = {};
                    for (var i = 0; i < output_view.variables.length; i++) {
                        filter[output_view.variables[i]] = true;
                    }
                    output_view.filter = filter;
                    output_view.generate_html = function() {
                        var template = output_templates['output-template-'+this.ELEMENT_TYPE];
                        var template_options = [];
                        for (var i = 0; i < this.variables.length; i++) {
                            var name = this.variables[i];
                            var ticked = this.filter[name];
                            template_options.push({ 'name' : name, 'ticked' : ticked });
                        }
                        return template({name: this.name, id: this.id, options: template_options});
                    };
                    output_view.refresh_control = function() {
                        if (this.tab_hidden || this.container_hidden) { return; }
                        var ctx = document.getElementById('output-template-'+this.ELEMENT_TYPE+'-graph-'+this.id).getContext("2d");
                        var vars2show = [];
                        var data2show = [];
                        var to_add = [];
                        for (var i = 0; i < this.variables.length; i++) {
                            var variable = this.variables[i];
                            if (this.filter[variable]) {
                                vars2show.push(variable);
                                to_add.push(i);
                            }
                        }
                        for (var i = 0; i < this.data.length; i++) {
                            var old_data = this.data[i];
                            var new_data = { name: old_data.name, values: [] };
                            for (var j = 0; j < to_add.length; j++) {
                                new_data.values.push(old_data.values[to_add[j]]);
                            }
                            data2show.push(new_data);
                        }
                        var cfg = charting.radar(vars2show, data2show);
                        if (this.chart != null) { this.chart.destroy(); }
                        this.chart = new Chart(ctx, cfg);
                    };
                    output_view.set_filter = function(value, checked) {
                        this.filter[value] = checked;
                        this.refresh_control();
                    };
                    output_view.hookup_events = function() {
                        var this_ref = this;
                        // Hack from GitHub issue comment to get bootstrap-multiselect working in BS4-beta
                        $('#output-template-'+this.ELEMENT_TYPE+'-dropdown-'+this.id).multiselect({
                            templates: {
                                li: '<li><a class="dropdown-item"><label class="m-0 pl-2 pr-0"></label></a></li>',
                                ul: ' <ul class="multiselect-container dropdown-menu p-1 m-0"></ul>',
                                button: '<button type="button" class="multiselect dropdown-toggle output-variable-btn" data-toggle="dropdown" data-flip="false"><span class="multiselect-selected-text"></span> <b class="caret"></b></button>',
                                filter: '<li class="multiselect-item filter"><div class="input-group m-0"><input class="form-control multiselect-search" type="text"></div></li>',
                                filterClearBtn: '<span class="input-group-btn"><button class="btn btn-secondary multiselect-clear-filter" type="button"><i class="fas fa-minus-circle"></i></button></span>'
                            },
                            buttonContainer: '<div class="output-template-'+this_ref.ELEMENT_TYPE+'-dropdown-div" />',
                            buttonClass: 'btn btn-secondary',
                            buttonTitle: function(options, select) { return 'Variables'; },
                            buttonText: function(options, select) { return ''; },
                            buttonWidth: '26px',
                            onChange: function(opt, checked, sel) {
                                this_ref.set_filter($(opt).val(), checked);
                            }
                        });
                        hookup_export_data_event(this);
                    };
                    return output_view;
                }
                if (type === 'Doughnut') {
                    output_view.ELEMENT_TYPE = 'doughnut';
                    output_view.variables = json_output['variables'];
                    output_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    output_view.refresh_control = function() {
                        refresh_chart_control(this, charting.doughnut(this.variables, this.data));
                    };
                    output_view.hookup_events = function() {
                        hookup_export_data_event(this);
                    };
                    return output_view;
                }
                if (type === 'Histogram') {
                    output_view.ELEMENT_TYPE = 'histogram';
                    output_view.intervals = json_output['intervals'];
                    output_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    output_view.refresh_control = function() {
                        refresh_chart_control(this, charting.histogram(this.intervals, this.data, this.display));
                    };
                    output_view.hookup_events = function() {
                        hookup_export_data_event(this);
                    };
                    return output_view;
                }
                if (type === 'Pie') {
                    output_view.ELEMENT_TYPE = 'pie';
                    output_view.variables = json_output['variables'];
                    output_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    output_view.refresh_control = function() {
                        refresh_chart_control(this, charting.pie(this.variables, this.data));
                    };
                    output_view.hookup_events = function() {
                        hookup_export_data_event(this);
                    };
                    return output_view;
                }
                if (type === 'Box') {
                    output_view.ELEMENT_TYPE = 'box';
                    output_view.variables = json_output['variables'];
                    output_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    output_view.refresh_control = function() {
                        refresh_chart_control(this, charting.box(this.variables, this.data, this.display));
                    };
                    output_view.hookup_events = function() {
                        hookup_export_data_event(this);
                    };
                    return output_view;
                }
                throw ('Output type "' + type + '" not recognised.');
            }

            return {
                create_output_view : create_output_view
            }
        }();

        function initialise_outputs() {
            var content_height = window.innerHeight - 240;
            jsPanel.create({
                theme: 'primary',
                contentSize: {
                    width: function() { return Math.min(400, window.innerWidth * 0.3); },
                    height: content_height
                },
                position: 'center-right -10 110',
                animateIn: 'jsPanelFadeIn',
                headerTitle: 'Salidas',
                container: $('#map-div'),
                content: '<div id="outputs-div"></div>',
                dragit: { containment: [110, 10, 50, 10] },
                maximizedMargin: [110, 10, 50, 10],
                headerControls: { 'close' : 'remove' }
            });
            $.get('get_outputs/', function(response) {
                var output_tab_template = io_common.compile_templates(['output-template-tabs'])['output-template-tabs'];
                io_common.get_variables(response, 'output', output_tab_template,
                model_outputs_view_factory.create_output_view, register_output_view, set_output_values, true, tab_hide_outputs, tab_show_outputs);
            }, 'json').fail(
                function(e) { report_server_error('get_outputs', e); }
            );
        }

        function register_output_view(output_view) {
            output_views[output_view.id] = output_view;
        }

        function set_output_values(output_values) {
            for (var id in output_values) {
                output_views[id].set_value(output_values[id]);
            }
        }

        function clear_outputs() {
            for (var id in output_views) {
                output_views[id].clear();
            }
        }

        function tab_hide_outputs(output_views) {
            for (var id in output_views) {
                output_views[id].tab_hide();
            }
        }

        function tab_show_outputs(output_views) {
            for (var id in output_views) {
                output_views[id].tab_show();
            }
        }

        function container_hide_outputs() {
            for (var id in output_views) {
                output_views[id].container_hide();
            }
        }

        function container_show_outputs() {
            for (var id in output_views) {
                output_views[id].container_show();
            }
        }

        return {
            initialise_outputs: initialise_outputs,
            set_output_values: set_output_values,
            clear_outputs: clear_outputs,
            container_hide_outputs: container_hide_outputs,
            container_show_outputs: container_show_outputs
        }
    }();

    // INPUT/OUTPUT COMMON

    var io_common = function() {

        function get_variables(io_response, ident, template, create_object_func, register_object_func, set_values_func, hideable, tab_hide_func, tab_show_func) {
            var group_template = compile_templates(['group-template'])['group-template'];
            io_response.sort(function(a,b) { if (a.index > b.index) { return 1; } else if (a.index < b.index) { return -1; } else { return 0; } });
            var get_groupings_args = {'input':(ident === 'input')}
            $.post('get_groupings/', JSON.stringify(get_groupings_args), function(group_response) {
                function attach_tooltip(element_id, contents, direction) {
                    var options = {
                        html: true,
                        placement: direction,
                        title: contents,
                        trigger: 'click',
                        boundary: 'window'
                    };
                    $('#'+element_id).tooltip(options);
                }
                function add_grouping_element(grouping, parent_element_id, type, ident) {
                    if (ident === 'input') {
                        var direction = 'right';
                    }
                    else {
                        var direction = 'left';
                    }
                    var id = type+'-'+grouping.id+'-div';
                    var hasinfo = grouping.info_html !== '';
                    var context = {type: type, name: grouping.name, hasinfo: hasinfo, id: id, direction: direction};
                    $('#'+parent_element_id).append(group_template(context));
                    if (grouping.info_html !== '') {
                        attach_tooltip(id+'-img', grouping.info_html, direction);
                    }
                }
                function get_controls(ios, group) {
                    result = [];
                    for (var i = 0; i < ios.length; i++) {
                        var io = ios[i];
                        if (io.grouping === group) {
                            result.push(io);
                        }
                    }
                    return result;
                }
                function build_and_add(ios, group_element_id, tab_index, lookup) {
                    for (var k = 0; k < ios.length; k++) {
                        var io_object = create_object_func(ios[k]);
                        if (tab_index > 0 && hideable) {
                            io_object.tab_hide();
                        }
                        var html = io_object.generate_html();
                        $('#'+group_element_id).append(html);
                        if (tab_index > 0) {
                            $('#'+group_element_id).hide();
                        }
                        io_object.hookup_events();
                        register_object_func(io_object);
                        if (lookup != null) {
                            lookup[group_element_id].push(io_object);
                        }
                    }
                }
                group_response.sort(function(a,b) { if (a.index > b.index) { return 1; } else if (a.index < b.index) { return -1; } else { return 0; } });
                if (group_response.length > 1) {
                    // TABS
                    // Build the tabs
                    var tab_groups = [];
                    for (var i = 0; i < group_response.length; i++) {
                        var group_item = { id: i+1, group: group_response[i].name };
                        tab_groups.push(group_item);
                    }
                    var context = { groups: tab_groups };
                    var group_html = template(context);
                    $('#'+ident+'s-div').append(group_html);
                    // Build the groups (tab contents)
                    var io_group_lookup = {};
                    for (var i = 0; i < group_response.length; i++) {
                        var id = i + 1;
                        var group_element_id = ident+'-tab-'+id;
                        if (!(group_element_id in io_group_lookup)) {
                            io_group_lookup[group_element_id] = [];
                        }
                        var group = group_response[i];
                        // Add Group element (and info button)
                        add_grouping_element(group, group_element_id, 'group', ident);
                        // Add Items
                        var gl = get_controls(io_response, group.id);
                        build_and_add(gl, group_element_id, i, io_group_lookup);
                        // Build the sub groups
                        for (var j = 0; j < group.subgroups.length; j++) {
                            var subgroup = group.subgroups[j];
                            // Add the subgroup title (and info button)
                            add_grouping_element(subgroup, group_element_id, 'subgroup', ident);
                            // Add Items
                            var sl = get_controls(io_response, subgroup.id);
                            build_and_add(sl, group_element_id, i, io_group_lookup);
                        }
                    }
                    // Handle tab show/hide
                    $('#'+ident+'-tabs-div').scrollTabs( {
                        click_callback: function(e) {
                            for (var id = 1; id <= tab_groups.length; id++) {
                                if (hideable) {
                                    tab_hide_func(io_group_lookup['output-tab-'+id]);
                                }
                                $('#'+ident+'-tab-'+id).hide();
                            }
                            var classes = e.target.getAttribute('class');
                            if (classes.indexOf('scroll_tab_left_finisher') >= 0) {
                                id = 1;
                            } else if (classes.indexOf('scroll_tab_right_finisher') >= 0) {
                                id = tab_groups.length;
                            } else {
                                id = e.target.getAttribute('ident');
                            }
                            $('#'+ident+'-tab-'+id).show();
                            if (hideable) {
                                tab_show_func(io_group_lookup['output-tab-'+id]);
                            }
                        }
                    });
                    $('#'+ident+'-tab-span-1').addClass('tab_selected');
                }
                else if (group_response.length == 1) {
                    // NO TABS
                    var group = group_response[0];
                    // Add Group element (and info button)
                    var group_element_id = ident+'s-div';
                    add_grouping_element(group, group_element_id, 'group', ident);
                    // Add Items
                    var gl = get_controls(io_response, group.id);
                    build_and_add(gl, group_element_id, 0, null);
                    // Build the sub groups
                    for (var j = 0; j < group.subgroups.length; j++) {
                        var subgroup = group.subgroups[j];
                        // Add the subgroup title (and info button)
                        add_grouping_element(subgroup, group_element_id, 'subgroup', ident);
                        // Add Items
                        var sl = get_controls(io_response, subgroup.id);
                        build_and_add(sl, group_element_id, 0, null);
                    }
                }
                else {
                    // NO TABS AND NO GROUPS
                    for (var k = 0; k < io_response.length; k++) {
                        var io_object = create_object_func(io_response[k]);
                        var html = io_object.generate_html();
                        $('#'+ident+'s-div').append(html);
                        io_object.hookup_events();
                        register_object_func(io_object);
                    }
                }
                $.get('get_all_'+ident+'_data/', function(response) {
                    set_values_func(response);
                }, 'json').fail(
                    function(e) { report_server_error('get_all_' + ident + '_data', e); }
                );
            }, 'json').fail(
                function(e) { report_server_error('get_groupings', e); }
            );
        }

        function compile_templates(template_names) {
            compiled_templates = {};
            for (var i = 0; i < template_names.length; i++) {
                var template_name = template_names[i];
                var source = document.getElementById(template_name).innerHTML;
                compiled_templates[template_name] = Handlebars.compile(source);
            }
            return compiled_templates;
        }
        
        return {
            get_variables : get_variables,
            compile_templates: compile_templates
        }
    }();

    // FEATURE FINDER

    var feature_finder = function() {

        const POINT_ZOOM_LEVEL = 15;

        var points_of_interest;

        function get_points_of_interest(callback) {
            points_of_interest = [];
            $.get('get_points_of_interest/', function(response) {
                for (var key in response) {
                    var poi = response[key];
                    points_of_interest.push(poi);
                }
                points_of_interest.sort(function(a,b) { if (a.name > b.name) { return 1; } else if (a.name < b.name) { return -1; } else { return 0; } });
            }, 'json').fail(
                function(e) { report_server_error('get_points_of_interest', e); }
            ).done(
                function() { callback(); }
            );
        }

        var feature_finder_template;
        var feature_finder_objects;
        var feature_finder_hash;

        function initialise_feature_finder(callback) {
            feature_finder_template = compile_feature_finder_template();
            feature_finder_objects = {};
            feature_finder_hash = -1;
            get_points_of_interest(callback);
        }

        function compile_feature_finder_template() {
            var source = document.getElementById('feature-finder-template').innerHTML;
            return Handlebars.compile(source);
        }

        function update_features(layer_objects) {
            var active_ids = [];
            for (var i = 0; i < layer_objects.length; i++) {
                var layer_object = layer_objects[i];
                if (layer_object.hasOwnProperty('features')) {
                    feature_finder_objects[layer_object.id] = { 'name' : layer_object.name, 'features' : layer_object.features };
                    active_ids.push(layer_object.id);
                }
            }
            var to_delete = [];
            for (var id in feature_finder_objects) {
                if (active_ids.indexOf(id) < 0) {
                    to_delete.push(id);
                }
            }
            for (var i = 0; i < to_delete.length; i++) {
                delete feature_finder_objects[to_delete[i]];
            }
        }

        function refresh_feature_finder() {
            var compute_pseudo_hash = function() {
                var string_hash = function(str) {
                    var hash = 0, i, chr;
                    if (str.length === 0) return hash;
                    for (var i = 0; i < str.length; i++) {
                        chr   = str.charCodeAt(i);
                        hash  = ((hash << 5) - hash) + chr;
                        hash |= 0;
                    }
                    return hash;
                }
                var hash = 0;
                for (key in feature_finder_objects) {
                    hash += string_hash(feature_finder_objects[key].name);
                    for (var i = 0; i < feature_finder_objects[key].features.length; i++) {
                        hash += string_hash(feature_finder_objects[key].features[i].name);
                    }
                }
                return hash;
            }
            var hash = compute_pseudo_hash();
            if (hash === feature_finder_hash) {
                return;//Only redo control IF feature layers have changed
            }
            var groups = [];
            var group_id = 1;
            // Add Points of Interest
            if (points_of_interest.length > 0) {
                var poi_features = [];
                for (var i = 0; i < points_of_interest.length; i++) {
                    var poi = points_of_interest[i];
                    poi_features.push({'name': poi.name, 'layer_id': '', 'index': i});
                }
                groups.push({'name': 'Puntos de interes', 'id': group_id, 'features': poi_features});
                group_id = group_id + 1;
            }
            // Add Features by Layer
            feature_finder_hash = hash;
            var template = feature_finder_template;
            var keys = [];
            for (var key in feature_finder_objects) {
                keys.push(key);
            }
            keys.sort(function(a,b) { if (a > b) { return 1; } else if (a < b) { return -1; } else { return 0; } });
            for (var i = 0; i < keys.length; i++) {
                var key = keys[i];
                var features = [];
                var layer_feature = feature_finder_objects[key];
                for (var j = 0; j < layer_feature.features.length; j++) {
                    var feature = layer_feature.features[j];
                    features.push({'name': feature.name, 'layer_id': key, 'index': j});
                }
                features.sort(function(a,b) { if (a.name > b.name) { return 1; } else if (a.name < b.name) { return -1; } else { return 0; } });
                if (features.length > 0) { // Only show layer heading if it has more than zero features
                    groups.push({'name': layer_feature.name, 'id': group_id, 'features': features});
                    group_id = group_id + 1;
                }
            }
            var context = {groups: groups, exists: (groups.length > 0)};
            var html = template(context);
            $('#feature-finder-div').empty();
            $('#feature-finder-div').append(html);
            // Setup search functionality
            setup_search();
        }

        function setup_search() {
            // Handle searching for features by pruning the layer feature tree
            var prune_features = function(search_text, match_case) {
                var groups = document.getElementsByClassName('feature-finder-group');
                for (var i = 0; i < groups.length; i++) {
                    var group = groups[i];
                    var viz_count = 0;
                    if (search_text != '') {
                        // Expand all groups while searching
                        $(group.getElementsByClassName('panel-collapse')[0]).collapse('show');
                    }
                    var features = group.getElementsByClassName('list-group-item');
                    for (var j = 0; j < features.length; j++) {
                        var li = features[j];
                        var val = li.getElementsByTagName('span')[0].innerHTML;
                        if (!match_case) {
                            val = val.toLowerCase();
                            search_text = search_text.toLowerCase();
                        }
                        if (val.indexOf(search_text) >= 0) {
                            viz_count = viz_count + 1;
                            li.style.display = 'block';
                        }
                        else {
                            li.style.display = 'none';
                        }
                    }
                    // Hide group headings if they contain no search results (do not animate hide/show for speed)
                    if (viz_count > 0) {
                        group.style.display = 'block';
                    }
                    else {
                        group.style.display = 'none';
                    }
                }
            };
            $('#feature-finder-search').on('input',function(e) {
                var search_text = $('#feature-finder-search').val();
                prune_features(search_text, false);
            });
            // Clear search textbox
            $('#feature-finder-clear').on('click',function(e) {
                $('#feature-finder-search').val('');
                $('#feature-finder-search').trigger('input');
            });
            // Expand and Collapse layer feature groups
            var expand_collapse_all = function(expand) {
                var action;
                if (expand) {
                    action = 'show';
                }
                else {
                    action = 'hide';
                }
                $('.feature-finder-group .panel-collapse').collapse(action);
            };
            $('#feature-finder-expand').on('click',function(e) {
                expand_collapse_all(true);
            });
            $('#feature-finder-collapse').on('click',function(e) {
                expand_collapse_all(false);
            });
        }

        function pan_map_to_feature(layer_id, index) {
            if (layer_id === '') {
                var poi = points_of_interest[index];
                map_base_manager.map.setView([poi.lat, poi.lon], poi.zoom, {animation: true});
            }
            else {
                var feature = feature_finder_objects[layer_id].features[index];
                if (feature.point != null) {
                    map_base_manager.map.setView([feature.point[1], feature.point[0]], POINT_ZOOM_LEVEL, {animation: true});
                    map_layer_manager.highlight_feature(layer_id, index);
                }
                else if (feature.bounds != null) {
                    map_base_manager.map.fitBounds(feature.bounds);
                    map_layer_manager.highlight_feature(layer_id, index);
                }
            }
        }

        function toggle_feature_finder() {
            if ($('#feature-finder-container').css('display') === 'none') {
                show_feature_finder();
            }
            else {
                hide_feature_finder();
            }
        }

        function hide_feature_finder() {
            $('#feature-finder-container').toggle('slow', function() {
                $('#feature-finder-btn-div').show();
            });
        }

        function show_feature_finder() {
            $('#feature-finder-container').toggle('slow');
        }

        return {
            initialise_feature_finder: initialise_feature_finder,
            update_features: update_features,
            refresh_feature_finder: refresh_feature_finder,
            pan_map_to_feature: pan_map_to_feature,
            toggle_feature_finder: toggle_feature_finder
        }
    }();

    // LAYER DATA DIALOGS

    var layer_data_dialogs = function() {

        var layer_data_views = [];

        var layer_data_view_factory = function() {

            var layer_data_templates;

            function compile_layer_data_templates() {
                return io_common.compile_templates([
                    'layer-data-dialog-template-default',
                    'layer-data-dialog-template-image'
                    ]);
            }

            function create_layer_data_view(control_id, json_layer_data, title) {
                // Common helper functions
                function build_default_template(view_obj) {
                    var template = layer_data_templates['layer-data-dialog-template-default'];
                    var context = {id: view_obj.control_id, type: view_obj.ELEMENT_TYPE};
                    return template(context);
                }
                function refresh_chart_control(view_obj, cfg) {
                    var ctx = document.getElementById('layer-data-dialog-template-'+view_obj.ELEMENT_TYPE+'-graph-'+view_obj.control_id).getContext("2d");
                    if (view_obj.chart != null) { view_obj.chart.destroy(); }
                    view_obj.chart = new Chart(ctx, cfg);
                }
                if (typeof layer_data_templates === 'undefined') {
                    layer_data_templates = compile_layer_data_templates();
                }
                // Common
                var type = json_layer_data['type'];
                var layer_data_view = {
                    data: [
                        {
                            id: json_layer_data['layer_id'],
                            type: json_layer_data['type'],
                            ident: json_layer_data['ident'],
                            title: title,
                            data: [],
                            display: json_layer_data['display']
                        }
                    ],
                    control_id: control_id,
                    markers: []
                }
                layer_data_view.get_data = function() {
                    return this.data;
                };
                layer_data_view.set_data = function(value) {
                    this.data = value;
                    this.refresh_control();
                };
                layer_data_view.clear = function() {
                    for (var i = 0; i < this.data.length; i++) {
                        this.data[i].data = [];
                    }
                    this.refresh_control();
                };
                layer_data_view.hookup_events = function() {};
                layer_data_view.destroy = function() {
                    remove_layer_data_dialog(this);
                };
                layer_data_view.save_or_copy_data = function()
                {
                    export_data.send_to_clipboard(this, origin='DIALOG');
                };
                // Specialize
                if (type === 'Gauge') {
                    layer_data_view.ELEMENT_TYPE = 'gauge';
                    layer_data_view.min = json_layer_data['min'];
                    layer_data_view.max = json_layer_data['max'];
                    layer_data_view.gauge = null;
                    layer_data_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    layer_data_view.refresh_control = function() {
                        if (this.gauge === null) {
                            var ctx = document.getElementById('layer-data-dialog-template-'+this.ELEMENT_TYPE+'-graph-'+this.control_id);
                            var cfg = charting.gauge(this.min, this.max, this.data[0].display);
                            this.gauge = new Gauge(ctx).setOptions(cfg);
                            this.gauge.maxValue = this.max;
                            this.gauge.setMinValue(this.min);
                            this.gauge.animationSpeed = 1;
                        }
                        $('#layer-data-dialog-template-'+this.ELEMENT_TYPE+'-graph-'+this.control_id).attr('title', this.data[0].data);
                        this.gauge.set(this.data[0].data);
                    };
                    return layer_data_view;
                }
                if (type === 'Image') {
                    layer_data_view.ELEMENT_TYPE = 'image';
                    layer_data_view.img = null;
                    layer_data_view.generate_html = function() {
                        var template = layer_data_templates['layer-data-dialog-template-image'];
                        var context = {id: this.control_id, type: this.ELEMENT_TYPE};
                        return template(context);
                    };
                    layer_data_view.refresh_control = function() {
                        if (this.img === null) {
                            var ident = this.data[0].data;
                            if (ident != null) {
                                var url = 'get_image/?id=' + ident;
                                var image_address = 'get_image/?id=' + ident;
                                $('#layer-data-template-'+this.ELEMENT_TYPE+'-image-'+this.control_id).prop('src', image_address);
                            }
                        } else {
                            $('#layer-data-template-'+this.ELEMENT_TYPE+'-image-'+this.control_id).prop('src', '');
                        }
                    };
                    layer_data_view.save_or_copy_data = function()
                    {
                        export_data.save_to_disk(this, origin='DIALOG');
                    };
                    return layer_data_view;
                }
                // Chart
                layer_data_view.chart = null;
                layer_data_view.destroy = function() {
                    if (this.chart != null) {
                        this.chart.destroy();
                    }
                    remove_layer_data_dialog(this);
                };
                if (type === 'TimeSeries') {
                    layer_data_view.ELEMENT_TYPE = 'timeseries';
                    layer_data_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    layer_data_view.refresh_control = function() {
                        refresh_chart_control(this, charting.multi_timeseries(this.data));
                    };
                    layer_data_view.hookup_events = function() {
                        $('#layer-data-dialog-template-timeseries-graph-'+this.control_id).draggable({appendTo:'body',helper:'clone',cursor:'crosshair'});
                        var this_obj = this;
                        var on_drop = function(evt, ui) {
                            var el = ui.draggable[0];
                            var from_control_id = el.id.substring(44);
                            var from_view = get_view_from_id(from_control_id);
                            var contains = function(obj, arr) {
                                for (var i = 0; i < arr.length; i++) {
                                    if (arr[i].id === obj.id && arr[i].type === obj.type && arr[i].ident === obj.ident) {
                                        return true;
                                    }
                                }
                                return false;
                            }
                            for (var i = 0; i < from_view.data.length; i++) {
                                var d = from_view.data[i];
                                if (contains(d, this_obj.data) || d.type != this_obj.data[0].type) {
                                    continue;
                                }
                                var m = from_view.markers[i];
                                var m_clone = L.marker([m._latlng.lat, m._latlng.lng]).bindTooltip(m._tooltip._content);
                                this_obj.markers.push(m_clone);
                                m_clone.addTo(map_base_manager.map);
                                this_obj.data.push(d);
                            }
                            this_obj.refresh_control();
                        }
                        $('#layer-data-dialog-template-timeseries-graph-'+this.control_id).droppable({drop:on_drop});
                        charting.attach_click_event_handler('layer-data-dialog-template-timeseries-graph-'+this.control_id, function(e) { this_obj.chart.resetZoom(); });
                    };
                    return layer_data_view;
                }
                if (type === 'TimeSeriesWithIntervals') {
                    layer_data_view.ELEMENT_TYPE = 'timeseries-with-intervals';
                    layer_data_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    layer_data_view.refresh_control = function() {
                        refresh_chart_control(this, charting.timeseries_with_intervals(this.data[0].data, this.data[0].display));
                    };
                    layer_data_view.hookup_events = function() {
                        var this_obj = this;
                        charting.attach_click_event_handler('layer-data-dialog-template-timeseries-with-intervals-graph-'+this.control_id, function(e) { this_obj.chart.resetZoom(); });
                    };
                    return layer_data_view;
                }
                if (type === 'Radar') {
                    layer_data_view.ELEMENT_TYPE = 'radar';
                    layer_data_view.variables = json_layer_data['variables'];
                    layer_data_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    layer_data_view.refresh_control = function() {
                        refresh_chart_control(this, charting.radar(this.variables, this.data[0].data));
                    };
                    return layer_data_view;
                }
                if (type === 'Doughnut') {
                    layer_data_view.ELEMENT_TYPE = 'doughnut';
                    layer_data_view.variables = json_layer_data['variables'];
                    layer_data_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    layer_data_view.refresh_control = function() {
                        refresh_chart_control(this, charting.doughnut(this.variables, this.data[0].data));
                    };
                    return layer_data_view;
                }
                if (type === 'Histogram') {
                    layer_data_view.ELEMENT_TYPE = 'histogram';
                    layer_data_view.intervals = json_layer_data['intervals'];
                    layer_data_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    layer_data_view.refresh_control = function() {
                        refresh_chart_control(this, charting.histogram(this.intervals, this.data[0].data, this.data[0].display));
                    };
                    return layer_data_view;
                }
                if (type === 'Pie') {
                    layer_data_view.ELEMENT_TYPE = 'pie';
                    layer_data_view.variables = json_layer_data['variables'];
                    layer_data_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    layer_data_view.refresh_control = function() {
                        refresh_chart_control(this, charting.pie(this.variables, this.data[0].data));
                    };
                    return layer_data_view;
                }
                if (type === 'Box') {
                    layer_data_view.ELEMENT_TYPE = 'box';
                    layer_data_view.variables = json_layer_data['variables'];
                    layer_data_view.generate_html = function() {
                        return build_default_template(this);
                    };
                    layer_data_view.refresh_control = function() {
                        refresh_chart_control(this, charting.box(this.variables, this.data[0].data, this.data[0].display));
                    };
                    return layer_data_view;
                }
                throw ('Layer data type "' + type + '" not recognised.');
            }

            return {
                create_layer_data_view: create_layer_data_view
            }
        }();

        function move_dialog_to_top(el_name) {
            var top_level = $(el_name).first().parent();
            top_level.detach();
            top_level.appendTo(document.body);
        }

        function get_view_from_id(control_id) {
            for (var i = 0; i < layer_data_views.length; i++) {
                if (layer_data_views[i].control_id === control_id) {
                    return layer_data_views[i];
                }
            }
            return null;
        }

        function layer_data_dialog_closed(event) {
            for (var i = 0; i < layer_data_views.length; i++) {
                var view = layer_data_views[i];
                if ('layer-data-dialog-' + view.control_id == event.detail) {
                    for (var i = 0; i < view.markers.length; i++) {
                        map_base_manager.map.removeLayer(view.markers[i]);
                    }
                    view.destroy();
                }
            }
        }

        function spawn_layer_data_dialog(layer_id, type, ident, title, latlng) {
            document.body.style.cursor = 'progress';
            var args = {'layer_id': layer_id, 'type': type, 'ident': ident};
            $.post('get_layer_data_info/', JSON.stringify(args), function(response) {
                if (response === null) {
                    return;
                }
                var uuidv4 = function() {
                    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                        return v.toString(16);
                    });
                };
                var control_id = uuidv4();
                response['ident'] = ident;
                var layer_data_view = layer_data_view_factory.create_layer_data_view(control_id, response, title);
                var p = jsPanel.create({
                    id: 'layer-data-dialog-' + control_id,
                    theme: 'primary',
                    contentSize: {
                        width: 350,
                        height: 200
                    },
                    position: 'center',
                    animateIn: 'jsPanelFadeIn',
                    headerTitle: title,
                    container: $('#map-div'),
                    content: '<div class="layer-data-content">' + layer_data_view.generate_html() + '</div>',
                    dragit: { containment: [110, 10, 50, 10] },
                    maximizedMargin: [110, 10, 50, 10]
                });
                p.headertitle.title = title;
                // Place marker where layer data was selected
                var marker = L.marker([latlng.lat, latlng.lng]).bindTooltip(title);
                layer_data_view.markers.push(marker);
                marker.addTo(map_base_manager.map);
                layer_data_view.hookup_events();
                register_layer_data_dialog(layer_data_view);
                update_layer_data_dialog(layer_data_view);
                document.body.style.cursor = 'auto';
            }, 'json').fail(
                function(e) { report_server_error('get_layer_data_info', e); }
            );
        }

        function register_layer_data_dialog(dialog_view) {
            layer_data_views.push(dialog_view);
            // Connect copy to clipboard event handler
            $('#layer-data-dialog-template-'+dialog_view.ELEMENT_TYPE+'-export-img-'+dialog_view.control_id).on('click', function() { dialog_view.save_or_copy_data(); })
        }

        function update_layer_data_dialog(dialog_view) {
            var data = dialog_view.get_data();
            var promises = [];
            for (var i = 0; i < data.length; i++) {
                var d = data[i];
                var args = {'layer_id': d.id, 'type': d.type, 'ident': d.ident};
                promises.push($.post('get_layer_data/', JSON.stringify(args), null, 'json'));
            }
            $.when.apply($, promises).then(function() {
                if (promises.length === 1) {
                    data[0].data = arguments[0];
                }
                else {
                    for (var i = 0; i < promises.length; i++) {
                        data[i].data = arguments[i][0];
                    }
                }
                dialog_view.set_data(data);
            }, function(e) {
                report_server_error('get_layer_data', e);
                for (var i = 0; i < data.length; i++) {
                    var d = data[i];
                    d.data = [];
                }
                dialog_view.set_data(data);
            });
        }

        function update_layer_data_dialogs() {
            for (var i = 0; i < layer_data_views.length; i++) {
                update_layer_data_dialog(layer_data_views[i]);
            }
        }

        function clear_layer_data_dialogs() {
            for (var i = 0; i < layer_data_views.length; i++) {
                layer_data_views[i].clear();
            }
        }

        function remove_layer_data_dialog(dialog_view) {
            var ind = -1;
            for (var i = 0; i < layer_data_views.length; i++) {
                if (layer_data_views[i] === dialog_view) {
                    ind = i;
                    break;
                }
            }
            if (ind > -1) {
                layer_data_views.splice(ind, 1);
            }
            // Disconnect copy to clipboard event handler
            $('#layer-data-dialog-template-'+dialog_view.ELEMENT_TYPE+'-export-img-'+dialog_view.control_id).off('click');
        }

        return {
            spawn_layer_data_dialog: spawn_layer_data_dialog,
            update_layer_data_dialogs: update_layer_data_dialogs,
            clear_layer_data_dialogs: clear_layer_data_dialogs,
            layer_data_dialog_closed: layer_data_dialog_closed
        }
    }();

    // EXPORT DATA

    var export_data = function() {

        var save_to_disk = function(view_obj, origin) {

            if (origin === 'OUTPUT') {
                var filename = view_obj.name;
                var data = view_obj.data;
            } else {
                var filename = view_obj.data[0].title;
                var data = view_obj.data[0].data;
            }

            var ident = data;
            if (ident == null) { return; }
            var url = 'get_image/?id=' + ident;

            var lnk = document.createElement('a');
            lnk.download = filename;
            lnk.href = url;
            document.body.appendChild(lnk);
            lnk.click();
            document.body.removeChild(lnk);
        }

        var send_to_clipboard = function(view_obj, origin) {

            var str = data_to_string(view_obj, origin);
            var el = document.createElement('textarea');
            el.value = str;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
        }

        var data_to_string = function(view_obj, origin, style='CSV') {

            var date_str = 'Fecha';
            var variables_str = 'Variables';
            var intervals_str = 'Intervalos';

            var type, data, name;
            if (origin === 'OUTPUT') {
                type = view_obj.type;
                data = view_obj.data;
                name = view_obj.name;
            }
            else {
                type = view_obj.data[0].type;
                data = view_obj.data[0].data;
                name = view_obj.data[0].title;
            }
            if (type === 'Numeric' || type === 'Gauge') {
                if (data == null) {
                    var val = null;
                } else {
                    var val = data;
                }
                return '"' + name + '"\n' + val;
            }
            if (type === 'TimeSeries') {
                data = view_obj.data;
                if (style === 'JSON') {
                    if (origin === 'OUTPUT') {
                        return '"' + view_obj.name + '"\n' + JSON.stringify(data, null, 2);
                    }
                    if (origin === 'DIALOG') {
                        var str = '';
                        for (var i = 0; i < data.length; i++) {
                            str += '"' + data[i].title + '"\n' + JSON.stringify(data[i].data, null, 2) + '\n';
                        }
                        return str;
                    }
                }
                if (style === 'CSV') {
                    if (origin === 'OUTPUT') {
                        if (data == null) {
                            var val = null;
                        } else {
                            var val = '';
                            for (var i = 0; i < data.length; i++) {
                                val += data[i]['date'] + ',' + data[i]['value'] + '\n';
                            }
                        }
                        return date_str + ',' + '"' + view_obj.name + '"\n' + val;
                    }
                    if (origin === 'DIALOG') {
                        if (data.length == 1) {
                            var val = date_str + ',' + '"' + data[0].title + '"\n';
                            for (var i = 0; i < data.length; i++) {
                                for (var j = 0; j < data[i].data.length; j++) {
                                    val += data[i].data[j]['Date'] + ',' + data[i].data[j]['Value'] + '\n';
                                }
                            }
                            return val;
                        } else {
                            return 'NOT IMPLEMENTED!';
                        }
                    }
                }
            }
            if (type === 'TimeSeriesWithIntervals') {
                if (style === 'JSON') {
                    var clone = JSON.parse(JSON.stringify(data));
                    for (var i = 0; i < clone.length; i++) {
                        var values = {};
                        values['upper'] = clone[i].values[0];
                        values['mean'] = clone[i].values[1];
                        values['lower'] = clone[i].values[2];
                        clone[i].values = values;
                    }
                    return '"' + name + '"\n' + JSON.stringify(clone, null, 2);
                }
                if (style === 'CSV') {
                    if (data == null) {
                        var val = null;
                    } else {
                        var val = '';
                        for (var i = 0; i < data.length; i++) {
                            val += data[i]['date'] + ',' + data[i]['values'][2] + ',' + data[i]['values'][1] + ',' + data[i]['values'][0] + '\n'
                        }
                    }
                    return date_str + ',' + '"' + name + ' (bajo)","' + name + ' (media)","' + name + ' (alto)"\n' + val;
                }
            }
            if (type === 'Radar' || type === 'Doughnut') {
                if (style === 'JSON') {
                    var clone = JSON.parse(JSON.stringify(data));
                    for (var i = 0; i < clone.length; i++) {
                         if (clone.length === 1) {
                             delete clone[0]['name'];
                         }
                         var values = {};
                         for (var j = 0; j < clone[i].values.length; j++) {
                             values[view_obj.variables[j]] = clone[i].values[j];
                         }
                         clone[i].values = values;
                    }
                    return '"' + name + '"\n' + JSON.stringify(clone, null, 2);
                }
                if (style === 'CSV') {
                    if (data == null) {
                        var val = null;
                    } else {
                        var val = '"' + variables_str + '",';
                        for (var i = 0; i < data.length; i++) {
                            var dname = data[i].name;
                            if (dname == null) {
                                val += '"' + name + '",';
                            }
                            else {
                                val += '"' + dname + '",';
                            }
                        }
                        val = val.slice(0,-1) + '\n';
                        for (var i = 0; i < view_obj.variables.length; i++) {
                            val += '"' + view_obj.variables[i] + '",';
                            for (var j = 0; j < data.length; j++) {
                                val += data[j].values[i] + ',';
                            }
                            val = val.slice(0,-1) + '\n';
                        }
                    }
                    if (view_obj.data.length == 1) {
                        return val;
                    } else {
                        return '"' + name + '"\n' + val;
                    }
                }
            }
            if (type === 'Histogram') {
                if (style === 'JSON') {
                    var clone = JSON.parse(JSON.stringify(data));
                    for (var i = 0; i < clone.length; i++) {
                         if (clone.length === 1) {
                             delete clone[0]['name'];
                         }
                         var values = {};
                         for (var j = 0; j < clone[i].values.length; j++) {
                             values[view_obj.intervals[j]] = clone[i].values[j];
                         }
                         clone[i].values = values;
                    }
                    return '"' + name + '"\n' + JSON.stringify(clone, null, 2);
                }
                if (style === 'CSV') {
                    if (data == null) {
                        var val = null;
                    } else {
                        var val = '"' + intervals_str + '",';
                        for (var i = 0; i < data.length; i++) {
                            var dname = data[i].name;
                            if (dname == null) {
                                val += '"' + name + '",';
                            }
                            else {
                                val += '"' + dname + '",';
                            }
                        }
                        val = val.slice(0,-1) + '\n';
                        for (var i = 0; i < view_obj.intervals.length; i++) {
                            val += '"' + view_obj.intervals[i] + '",';
                            for (var j = 0; j < data.length; j++) {
                                val += data[j].values[i] + ',';
                            }
                            val = val.slice(0,-1) + '\n';
                        }
                    }
                    if (view_obj.data.length == 1) {
                        return val;
                    } else {
                        return '"' + name + '"\n' + val;
                    }
                }
            }
            if (type === 'Pie') {
                if (style === 'JSON') {
                    var values = {};
                    for (var i = 0; i < data.length; i++) {
                        values[view_obj.variables[i]] = data[i];
                    }
                    return '"' + name + '"\n' + JSON.stringify(values, null, 2);
                }
                if (style === 'CSV') {
                    if (data == null) {
                        var val = null;
                    } else {
                        var val = '';
                        for (var i = 0; i < view_obj.variables.length; i++) {
                            val += '"' + view_obj.variables[i] + '",' + data[i] + '\n';
                        }
                    }
                    return '"' + variables_str + '","' + name + '"\n' + val;
                }
            }
            if (type === 'Box') {
                var clone = JSON.parse(JSON.stringify(data));
                for (var i = 0; i < clone.length; i++) {
                    if (clone.length === 1) {
                        delete clone[0]['name'];
                    }
                    for (var j = 0; j < clone[i].values.length; j++) {
                        clone[i].values[j]['variable'] = view_obj.variables[j];
                    }
                }
                return '"' + name + '"\n' + JSON.stringify(clone, null, 2);
            }
            return '';
        }

        return {
            send_to_clipboard: send_to_clipboard,
            save_to_disk: save_to_disk
        }
    }();

    // CHARTING SUPPORT

    var charting = function() {

        const DEFAULT_TOOLTIP_DECIMAL_PLACES = 3;

        function invert_color(hex) {
            function padZero(str, len) {
                len = len || 2;
                var zeros = new Array(len).join('0');
                return (zeros + str).slice(-len);
            }
            if (hex.indexOf('#') === 0) {
                hex = hex.slice(1);
            }
            if (hex.length === 3) {
                hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
            }
            if (hex.length !== 6) {
                throw new Error('Invalid HEX color.');
            }
            var r = (255 - parseInt(hex.slice(0, 2), 16)).toString(16),
                g = (255 - parseInt(hex.slice(2, 4), 16)).toString(16),
                b = (255 - parseInt(hex.slice(4, 6), 16)).toString(16);
            return '#' + padZero(r) + padZero(g) + padZero(b);
        }

        function prc_str(v, dp) {
            if (dp == null || dp === -1) {
                return v;
            }
            var n = Math.pow(10, dp);
            return (Math.round(v * n) / n);
        }

        function get_timestep_of_data(dates) {
            if (dates.length < 2) {
                return timestep.create_timestep(timestep.sim_ts);
            }
            var diff = moment(dates[1]) - moment(dates[0]);
            diff = diff / 1000.0 / 60.0 / 60.0; // Milliseconds to Hours
            if (diff < 24.0) { // If less than 1 day - assume Hourly
                return timestep.create_timestep('Hourly');
            } else if (diff >= 672.0 && diff <= 744.0) { // If between 28 and 31 days - assume Monthly
                return timestep.create_timestep('Monthly');
            } else if (diff >= 8640.0) { // If over 360 days - assume Annual
                return timestep.create_timestep('Annual');
            } else {
                return timestep.create_timestep('Daily'); // Else assume Daily
            }
        }

        function register_chart_plugins() {
            Chart.plugins.register({
                id: 'filler',
                afterDatasetsDraw: function(chart) {
                    var lineTo = function(ctx, p0, p1, invert) {
                        if (p1.steppedLine === true) {
                            ctx.lineTo(p1.x, p0.y);
                            ctx.lineTo(p1.x, p1.y);
                        } else if (p1.tension === 0) {
                            ctx.lineTo(p1.x, p1.y);
                        } else {
                            ctx.bezierCurveTo(
                                invert? p0.controlPointPreviousX : p0.controlPointNextX,
                                invert? p0.controlPointPreviousY : p0.controlPointNextY,
                                invert? p1.controlPointNextX : p1.controlPointPreviousX,
                                invert? p1.controlPointNextY : p1.controlPointPreviousY,
                                p1.x,
                                p1.y
                            );
                        }
                    }
                    var options = chart.config.options.plugins.filler;
                    var datasets = chart.data.datasets;
                    var ctx = chart.chart.ctx;
                    (options.areas || []).forEach(function(area) {
                        var md0 = chart.getDatasetMeta(area.from) || {};
                        var md1 = chart.getDatasetMeta(area.to) || {};
                        if (md0.type !== 'line' || md1.type !== 'line') { return; }
                        var line0 = md0.dataset;
                        var line1 = md1.dataset;
                        var points0 = line0._children;
                        var points1 = line1._children;
                        var count = Math.min(points0.length, points1.length);
                        if (!count) { return; }
                        ctx.fillStyle = area.backgroundColor || line0._view.backgroundColor;
                        var min_x = chart.chartArea.left;
                        var max_x = chart.chartArea.right;
                        var p00, p01, p10, p11;
                        var cutoff_left, cutoff_right;
                        for (var i=0; i<count-1; ++i) {
                            p00 = points0[i]._view;
                            p01 = points0[i+1]._view;
                            p10 = points1[i]._view;
                            p11 = points1[i+1]._view;
                            if ((p00.x <= min_x && p01.x <= min_x) || (p00.x >= max_x && p01.x >= max_x)) { continue; }
                            var cutoff_left = p00.x < min_x && p01.x > min_x;
                            var cutoff_right = p00.x < max_x && p01.x > max_x;
                            var p00_copy, p01_copy, p10_copy, p11_copy;
                            if (cutoff_left || cutoff_right) {
                                p00_copy = JSON.parse(JSON.stringify(p00));
                                p01_copy = JSON.parse(JSON.stringify(p01));
                                p10_copy = JSON.parse(JSON.stringify(p10));
                                p11_copy = JSON.parse(JSON.stringify(p11));
                            }
                            else {
                                p00_copy = p00;
                                p01_copy = p01;
                                p10_copy = p10;
                                p11_copy = p11;
                            }
                            if (cutoff_left) {
                                var m, b, y_int;
                                m = (p01.y - p00.y) / (p01.x - p00.x);
                                b = p00.y - (m * p00.x);
                                y_int = (m * min_x) + b;
                                p00_copy.x = min_x;
                                p00_copy.y = y_int;
                                m = (p11.y - p10.y) / (p11.x - p10.x);
                                b = p10.y - (m * p10.x);
                                y_int = (m * min_x) + b;
                                p10_copy.x = min_x;
                                p10_copy.y = y_int;
                            }
                            if (cutoff_right) {
                                var m, b, y_int;
                                m = (p01.y - p00.y) / (p01.x - p00.x);
                                b = p01.y - (m * p01.x);
                                y_int = (m * max_x) + b;
                                p01_copy.x = max_x;
                                p01_copy.y = y_int;
                                m = (p11.y - p10.y) / (p11.x - p10.x);
                                b = p11.y - (m * p11.x);
                                y_int = (m * max_x) + b;
                                p11_copy.x = max_x;
                                p11_copy.y = y_int;
                            }
                            ctx.beginPath();
                            ctx.moveTo(p00_copy.x, p00_copy.y);
                            lineTo(ctx, p00_copy, p01_copy);
                            ctx.lineTo(p11_copy.x, p11_copy.y);
                            lineTo(ctx, p11_copy, p10_copy, true);
                            ctx.closePath();
                            ctx.fill();
                        }
                    });
                }
            });
        }

        function attach_click_event_handler(element_id, click_event_handler) {
            // This is used to differentiate between a click (on which we want to reset the zoom) and a drag (which also fires the click event) which performs a zoom-in.
            var isDragging = false;
            var startingPos = [];
            var mouse_move_tol = 1;
            $('#'+element_id).on('mousedown', function(e) { isDragging = false; startingPos = [e.pageX, e.pageY]; } );
            $('#'+element_id).on('mousemove', function(e) { if (Math.abs(e.pageX - startingPos[0]) > mouse_move_tol || Math.abs(e.pageY - startingPos[1]) > mouse_move_tol) { isDragging = true; } } );
            $('#'+element_id).on('mouseup', function(e) { if (!isDragging) { click_event_handler(e); isDragging = false; startingPos = []; } } );
        }

        function hexToRgb(hex) {
            var shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
            hex = hex.replace(shorthandRegex, function(m, r, g, b) {
                return r + r + g + g + b + b;
            });
            var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16),
                g: parseInt(result[2], 16),
                b: parseInt(result[3], 16)
            } : null;
        }

        function get_rgb(hex) {
            var c = hexToRgb(hex);
            return 'rgb('+c.r+','+c.g+','+c.b+')';
        }

        function get_rgba(hex, alpha) {
            
            var c = hexToRgb(hex);
            return 'rgba('+c.r+','+c.g+','+c.b+','+alpha+')';
        }

        function get_hex(r, g, b) {
            function componentToHex(c) {
                var hex = c.toString(16);
                return hex.length == 1 ? '0' + hex : hex;
            };
            return '#' + componentToHex(r) + componentToHex(g) + componentToHex(b);
        }

        function create_timeseries_dataset(label, rgba, data, pointRadius, fill) {
            return {
                label: label,
                backgroundColor: rgba,
                borderColor: rgba,
                data: data,
                type: 'line',
                pointRadius: pointRadius,
                fill: fill,
                lineTension: 0,
                borderWidth: 2
            }
        }

        function generate_timeseries_config(labels, datasets, display_legend, x_label, y_label, decimal_places) {
            var ts = get_timestep_of_data(labels);
            var time_format = ts.moment_format();
            var unit = ts.chart_unit(labels.length);
            var min_x = labels[0];
            var max_x = labels[labels.length-1];
            var display_x_label = true;
            if (x_label === null) { display_x_label = false; }
            var display_y_label = true;
            if (y_label === null) { display_y_label = false; }
            return {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    scales: {
                        xAxes: [{
                            type: 'time',
                            time: {
                                parser: time_format,
                                unit: unit
                            },
                            scaleLabel: {
                                display: display_x_label,
                                labelString: x_label
                            }
                        }],
                        yAxes: [{
                            scaleLabel: {
                                display: display_y_label,
                                labelString: y_label
                            }
                        }]
                    },
                    legend: {
                        display: display_legend
                    },
                    hover: {
                        mode: 'x',
                        intersect: false
                    },
                    tooltips: {
                        enabled: true,
                        callbacks: {
                            title: function(tooltipItem, data) {
                                return tooltipItem[0].xLabel.format(time_format);
                            },
                            label: function(tooltipItem, data) {
                                var label =  data.datasets[tooltipItem.datasetIndex].label || '';
                                if (label) {
                                    label += ': ';
                                }
                                var value = prc_str(data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index], decimal_places);
                                label += value;
                                return label;
                            }
                        }
                    },
                    maintainAspectRatio: false,
                    animation: false,
                    responsive: !IS_IE,
                    layout: {
                        padding: {
                            left: 15
                        }
                    },
                    zoom: {
                        enabled: true,
                        drag: true,
                        mode: 'x',
                        rangeMin: {
                            x: 0,
                            y: null
                        },
                        rangeMax: {
                            x: (max_x - min_x),
                            y: null
                        }
                    }
                }
            }
        }

        function timeseries(data, display) {
            var labels = [];
            var tsdata = [];
            for (var i = 0; i < data.length; i++) {
                labels.push(moment(data[i]['date']));
                tsdata.push(data[i]['value']);
            }
            var rgba = get_rgba('#428bca', 1.0);
            var pointRadius = 0;
            var fill = false;
            if (tsdata.length === 1) {
                pointRadius = 2;
                fill = true;
            }
            var datasets = [create_timeseries_dataset('', rgba, tsdata, pointRadius, fill)];
            return generate_timeseries_config(labels, datasets, false, display['x-label'], display['y-label'], display['decimal-places']);
        }

        function timeseries_with_intervals(data, display) {
            var labels = [];
            var int1 = [];
            var mean = [];
            var int2 = [];
            for (var i = 0; i < data.length; i++) {
                var date = moment(data[i]['date']);
                labels.push(date);
                int1.push(data[i]['values'][0]);
                mean.push(data[i]['values'][1]);
                int2.push(data[i]['values'][2]);
            }
            var rgba = get_rgba('#428bca', 0.3);
            var pointRadius = 0;
            var fill = false;
            if (data.length === 1) {
                pointRadius = 2;
                fill = true;
            }
            var datasets = [];
            datasets.push(create_timeseries_dataset('', rgba, int1, pointRadius, fill));
            datasets.push(create_timeseries_dataset('', rgba, mean, pointRadius, fill));
            datasets.push(create_timeseries_dataset('', rgba, int2, pointRadius, fill));
            var cfg = generate_timeseries_config(labels, datasets, false, display['x-label'], display['y-label'], display['decimal-places']);
            cfg.options.plugins = {
                filler: {
                    areas: [{
                        from: 0,
                        to: 1
                    }, {
                        from: 1,
                        to: 2
                    }]
                }
            }
            return cfg;
        }

        function create_radar_dataset(label, rgba, data) {
            return {
                label: label,
                backgroundColor: rgba,
                borderColor: rgba,
                pointBackgroundColor: rgba,
                fill: true,
                data: data
            }
        }

        function generate_radar_config(labels, datasets, decimal_places) {
            var legend = false;
            if (datasets.length > 1) { legend = { position: 'top' } }
            return {
                type: 'radar',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    legend: legend,
                    animation: false,
                    responsive: !IS_IE,
                    maintainAspectRatio: false,
                    tooltips: {
                        callbacks: {
                            title: function(items, data) {
                                if (items.length > 0) {
                                    return data.labels[items[0].index];
                                }
                                return '';
                            },
                            label: function(tooltipItem, data) {
                                var label =  data.datasets[tooltipItem.datasetIndex].label || '';
                                if (label) {
                                    label += ': ';
                                }
                                var value = prc_str(data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index], decimal_places);
                                label += value;
                                return label;
                            }
                        }
                    }
                }
            }
        }

        function radar(labels, data) {
            var colors = palette('tol-rainbow', data.length);
            var datasets = [];
            for (var i = 0; i < data.length; i++) {
                datasets.push(create_radar_dataset(data[i]['name'], get_rgba(colors[i], 0.2), data[i]['values']));
            }
            return generate_radar_config(labels, datasets, DEFAULT_TOOLTIP_DECIMAL_PLACES);
        }

        function create_doughnut_dataset(label, rgbas, data) {
            return {
                label: label,
                backgroundColor: rgbas,
                borderColor: rgbas,
                pointBackgroundColor: rgbas,
                fill: true,
                data: data
            }
        }

        function generate_doughnut_config(labels, datasets, decimal_places) {
            return {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    legend: { position: 'right' },
                    animation: false,
                    responsive: !IS_IE,
                    maintainAspectRatio: false,
                    tooltips: {
                        callbacks: {
                            title: function(items, data) {
                                if (items.length > 0) {
                                    return data.labels[items[0].index];
                                }
                                return '';
                            },
                            label: function(tooltipItem, data) {
                                var label =  data.datasets[tooltipItem.datasetIndex].label || '';
                                if (label) {
                                    label += ': ';
                                }
                                var value = prc_str(data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index], decimal_places);
                                label += value;
                                return label;
                            }
                        }
                    }
                }
            }
        }

        function doughnut(labels, data) {
            var n_colors = 0;
            for (var i = 0; i < data.length; i++) {
                var n = data[i]['values'].length;
                if (n > n_colors) { n_colors = n; }
            }
            var colors = palette('tol-rainbow', n_colors);
            var rgbas = [];
            for (var i = 0; i < colors.length; i++) {
                rgbas.push(get_rgba(colors[i], 0.8));
            }
            var datasets = [];
            for (var i = 0; i < data.length; i++) {
                datasets.push(create_doughnut_dataset(data[i]['name'], rgbas, data[i]['values']));
            }
            return generate_doughnut_config(labels, datasets, DEFAULT_TOOLTIP_DECIMAL_PLACES);
        }

        function create_histogram_dataset(label, rgba, data) {
            return {
                label: label,
                backgroundColor: rgba,
                borderColor: rgba,
                pointBackgroundColor: rgba,
                fill: true,
                data: data
            }
        }

        function generate_histogram_config(labels, datasets, x_label, y_label, decimal_places) {
            var legend = false;
            if (datasets.length > 1) { legend = { position: 'top' } }
            var display_x_label = true;
            if (x_label === null) { display_x_label = false; }
            var display_y_label = true;
            if (y_label === null) { display_y_label = false; }
            return {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    legend: legend,
                    animation: false,
                    responsive: !IS_IE,
                    maintainAspectRatio: false,
                    scales: {
                        xAxes: [{
                            scaleLabel: {
                                display: display_x_label,
                                labelString: x_label
                            }
                        }],
                        yAxes: [{
                            scaleLabel: {
                                display: display_y_label,
                                labelString: y_label
                            }
                        }]
                    },
                    tooltips: {
                        enabled: true,
                        callbacks: {
                            title: function(items, data) {
                                if (items.length > 0) {
                                    return data.labels[items[0].index];
                                }
                                return '';
                            },
                            label: function(tooltipItem, data) {
                                var label =  data.datasets[tooltipItem.datasetIndex].label || '';
                                if (label) {
                                    label += ': ';
                                }
                                var value = prc_str(data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index], decimal_places);
                                label += value;
                                return label;
                            }
                        }
                    }
                }
            }
        }

        function histogram(labels, data, display) {
            var colors = palette('tol-rainbow', data.length);
            var datasets = [];
            for (var i = 0; i < data.length; i++) {
                datasets.push(create_histogram_dataset(data[i]['name'], get_rgba(colors[i], 0.5), data[i]['values']));
            }
            return generate_histogram_config(labels, datasets, display['x-label'], display['y-label'], display['decimal-places']);
        }

        function create_pie_dataset() {
            return {
                label: '',
                backgroundColor: [],
                data: []
            }
        }

        function generate_pie_config(labels, datasets, decimal_places) {
            var cfg = {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    legend: { position: 'right' },
                    animation: false,
                    responsive: !IS_IE,
                    maintainAspectRatio: false,
                    tooltips: {
                        enabled: true,
                        callbacks: {
                            title: function(items, data) {
                                if (items.length > 0) {
                                    return data.labels[items[0].index];
                                }
                                return '';
                            },
                            label: function(tooltipItem, data) {
                                var label =  data.datasets[tooltipItem.datasetIndex].label || '';
                                if (label) {
                                    label += ': ';
                                }
                                var value = prc_str(data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index], decimal_places);
                                label += value;
                                return label;
                            }
                        }
                    }
                }
            }
            return cfg;
        }

        function pie(labels, data) {
            var colors = palette('tol-rainbow', data.length);
            var dataset = create_pie_dataset();
            for (var i = 0; i < data.length; i++) {
                dataset.backgroundColor.push(get_rgba(colors[i], 0.8));
                dataset.data.push(data[i]);
            }
            return generate_pie_config(labels, [dataset], DEFAULT_TOOLTIP_DECIMAL_PLACES);
        }

        function create_box_dataset(label, rgba, data) {
            return {
                label: label,
                backgroundColor: rgba,
                borderColor: '#000000',
                borderWidth: 1,
                data: data,
                padding: 0.1
            }
        }

        function generate_box_config(labels, datasets, x_label, y_label, decimal_places) {
            var legend = false;
            if (datasets.length > 1) { legend = { position: 'top' } }
            var display_x_label = true;
            if (x_label === null) { display_x_label = false; }
            var display_y_label = true;
            if (y_label === null) { display_y_label = false; }
            return {
                type: 'horizontalBoxplot',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    legend: legend,
                    animation: false,
                    responsive: !IS_IE,
                    maintainAspectRatio: false,
                    scales: {
                        xAxes: [{
                            scaleLabel: {
                                display: display_x_label,
                                labelString: x_label
                            }
                        }],
                        yAxes: [{
                            scaleLabel: {
                                display: display_y_label,
                                labelString: y_label
                            }
                        }]
                    },
                    tooltips: {
                        enabled: true,
                        callbacks: {
                            title: function(items, data) {
                                if (items.length > 0) {
                                    return data.labels[items[0].index];
                                }
                                return '';
                            },
                            label: function(tooltipItem, data) {
                                var label =  data.datasets[tooltipItem.datasetIndex].label || '';
                                if (label) {
                                    label += ': ';
                                }
                                var d = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index];
                                var min = prc_str(d['min'], decimal_places);
                                var q1 = prc_str(d['q1'], decimal_places);
                                var median = prc_str(d['median'], decimal_places);
                                var q3 = prc_str(d['q3'], decimal_places);
                                var max = prc_str(d['max'], decimal_places);
                                label += '(minimo: '+min+', q1: '+q1+', mediana: '+median+', q3: '+q3+', maximo: '+max+')'
                                return label;
                            }
                        }
                    }
                }
            }
        }

        function box(labels, data, display) {
            var colors = palette('tol-rainbow', data.length);
            var datasets = [];
            for (var i = 0; i < data.length; i++) {
                datasets.push(create_box_dataset(data[i]['name'], get_rgba(colors[i], 0.5), data[i]['values']));
            }
            return generate_box_config(labels, datasets, display['x-label'], display['y-label'], display['decimal-places']);
        }

        function gauge(min, max, display) {
            var cfg = {
                angle: 0,
                lineWidth: 0.42,
                radiusScale: 0.8,
                pointer: {
                    length: 0.61,
                    strokeWidth: 0.057,
                    color: '#000000'
                },
                limitMax: true,
                limitMin: true,
                colorStart: '#6FADCF',
                colorStop: '#8FC0DA',
                strokeColor: '#E0E0E0',
                generateGradient: true,
                highDpiSupport: true,
                staticLabels: {
                    font: "10px sans-serif",
                    labels: [min, max],
                    color: "#000000",
                    fractionDigits: 0
                },
            }
            if (display != null) {
                if (display.labels.labels.length > 0) {
                    cfg.staticLabels.labels = display.labels.labels;
                    cfg.staticLabels.fractionDigits = display.labels.decimal_places;
                }
                if (display.percent.length > 0) {
                    cfg.percentColors = display.percent;
                }
                else if (display.zones.length > 0) {
                    var staticZones = [];
                    for (var i = 0; i < display.zones.length; i++) {
                        var zone = display.zones[i];
                        staticZones.push({ strokeStyle: zone.color, min: zone.min, max: zone.max });
                    }
                    cfg.staticZones = staticZones;
                }
            }
            return cfg;
        }

        function multi_timeseries(data) {
            var colors = palette('mpn65', data.length);
            var labels = [];
            var datasets = [];
            for (var i = 0; i < data.length; i++) {
                var tsdata = [];
                for (var j = 0; j < data[i].data.length; j++) {
                    if (i === 0) { labels.push(moment(data[i].data[j]['Date'])); }
                    tsdata.push(data[i].data[j]['Value']);
                }
                var rgba = get_rgba(colors[i], 1.0);
                var pointRadius = 0;
                var fill = false;
                if (tsdata.length === 1) {
                    pointRadius = 2;
                    fill = true;
                }
                datasets.push(create_timeseries_dataset(data[i].title, rgba, tsdata, pointRadius, fill));
            }
            var display_legend = datasets.length > 1;
            return generate_timeseries_config(labels, datasets, display_legend, data[0].display['x-label'], data[0].display['y-label'], data[0].display['decimal-places']);
        }

        return {
            invert_color: invert_color,
            register_chart_plugins: register_chart_plugins,
            attach_click_event_handler: attach_click_event_handler,
            timeseries: timeseries,
            timeseries_with_intervals: timeseries_with_intervals,
            radar: radar,
            doughnut: doughnut,
            histogram: histogram,
            pie: pie,
            box: box,
            gauge: gauge,
            multi_timeseries: multi_timeseries
        }
    }();

    // TIME STEP HELPER

    var timestep = function() {

        var sim_ts;

        var create_timestep = function(ts) {
            var time_step = {};
            time_step.ts = ts;
            time_step.moment_format = function() {
                if (this.ts === 'Hourly') { return 'HH:mm DD/MM/YYYY'; }
                if (this.ts === 'Daily') { return 'DD/MM/YYYY'; }
                if (this.ts === 'Monthly') { return 'MM/YYYY'; }
                if (this.ts === 'Annual') { return 'YYYY'; }
            };
            time_step.chart_unit = function(num_points) {
                if (this.ts === 'Hourly') {
                    if (num_points < 24) { return 'hour'; }
                    else { return ''; }
                }
                if (this.ts === 'Daily') {
                    if (num_points < 31) { return 'day'; }
                    else { return ''; }
                }
                if (this.ts === 'Monthly') {
                    if (num_points < 12) { return 'month'; }
                    else { return ''; }
                }
                if (this.ts === 'Annual') { return 'year'; }
            };
            return time_step;
        }

        return {
            sim_ts: sim_ts,
            create_timestep: create_timestep
        }
    }();

    // AJAX ERROR HANDLING

    function report_server_error(action, e) {
        var exception_type = 'Ha ocurrido un error en el servidor web!';
        var exception_details = 'Falla en la operacion del servidor: ' + action + '. El servidor devolvio el codigo: ' + e.status + ' - ' + e.statusText + '.';
        document.getElementById('scenario-exception-modal-type').innerHTML = exception_type;
        document.getElementById('scenario-exception-modal-details').innerHTML = exception_details;
        $('#scenario-exception-modal').modal('show');
    }

    // PUBLIC FUNCTIONS

    return {
        initialise_main: initialise_main,
        run_scenario: scenario.run_scenario,
        reset_scenario: scenario.reset_scenario,
        toggle_feature_finder: feature_finder.toggle_feature_finder,
        pan_map_to_feature: feature_finder.pan_map_to_feature,
        export_results: scenario.export_results
    }
}());