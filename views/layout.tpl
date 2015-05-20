% include header title=title
  <body>
    <div class="body">
        <h1>{{title}}</h1>
            <p>
              {% for s, duration, updatetime in section_durations %}
              {{s}} : {{duration}} ({{updatetime}})<br>
              {% endfor %}
            </p>
            <p>
              <img src="data:image/png;base64,{{figure}}" alt="Temps de parcours" width=90%><br>
            </p>
    </div>
  </body>
</html>
