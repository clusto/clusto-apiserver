<head>
  <title>Clusto:</title>
  <link href="{{app.get_url('static',filename='bootstrap/css/bootstrap.min.css')}}" rel="stylesheet" type="text/css">
  <link href="{{app.get_url('static',filename='css/screen.css')}}" rel="stylesheet" type="text/css">
</head>
<body style="padding-top: 40px;">
  <div class="navbar navbar-inverse navbar-fixed-top">
    <div class="navbar-inner">
          <a class="brand" href="{{ app.get_url('/') }}">Clusto API Server</a>
      <div class="container" style="font-wize:1vw">
        <ul class="nav" style="">
          % for name, drivernames in typelist.items():
          <li class="dropdown">
            <a class="dropdown-toggle" data-toggle="dropdown" href="{{ app.get_url('typeview', typename=name) }}" style="text-transform:capitalize;">{{ name }}s</a>
              <ul class="dropdown-menu">
                 % for drivername in drivernames:
                 <li><a href="{{ app.get_url('driverview', drivername=drivername.__name__.lower()) }}">{{ drivername.__name__ }}</a></li>
                 % end
             </ul>
          </li>
          % end
        </ul>
      </div>
    </div>
  </div>
  <div class="container-fluid">
</body>
<body>
  <script>src="{{ app.get_url('static', filename='js/jquery-1.7.2.min.js') }}"</script>
  <script>src="{{ app.get_url('static', filename='bootstrap/js/bootstrap.js') }}"</script>
</body>
