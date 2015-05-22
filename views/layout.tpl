% include header title=title
  <body>
    <div class="body">
        <h1>{{title}}</h1>
            <p>
              {% for section, duration, time  in section_durations %}
              {{section}} : {{duration}} ({{time}})<br>
              {% endfor %}
            </p>
    </div>
  </body>
</html>
