% include header title=title
  <body>
    <div class="body">
        <h1>{{title}}</h1>
            <p>
              {% for s in section_durations %}
              {{s[¯]}} : {{s[1]}} ({{s[2]}})<br>
              {% endfor %}
            </p>
    </div>
  </body>
</html>
