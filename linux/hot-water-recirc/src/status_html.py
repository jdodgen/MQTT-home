html = """
<!DOCTYPE html>
<html lang="en">
<body>
  <h1>Hot Water Controller Activity</h1>
  <h2 id="status"></h2>
  <script>
    var eventSource = new EventSource("/listen")
    eventSource.addEventListener("online", function(e) {
      data = JSON.parse(e.data)
      document.querySelector("body").style.backgroundColor= data.color
      document.querySelector("#status").innerText = data.status
    }, true)
  </script>
</body>
</html>
"""
