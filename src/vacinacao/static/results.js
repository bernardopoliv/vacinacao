function createColumns(result, row) {
  for (let field in result) {
    let col = document.createElement("td");
    let text = document.createTextNode(result[field])
    col.appendChild(text)
    row.appendChild(col)
  }
}

function createRows(response) {
  const resultsBody = document.getElementById('results')
  response.forEach(function (result) {
    var row = document.createElement("tr");
    createColumns(result, row)
    resultsBody.appendChild(row)
  })
}

function removeResults(elementId) {
  const results = document.getElementById(elementId);
  while (results.firstChild) {
    results.removeChild(results.lastChild);
  }
}

document.getElementById('search').addEventListener('click', function () {
  const noInputWarning = document.getElementById('no-input-warning')
  const nameInput = document.getElementById('name')
  const name = nameInput.value
  if (!name.trim()) {
    noInputWarning.style.display = ''  // Visible
  } else {
    noInputWarning.style.display = 'none'  // Invisible

    postData('/search', {name: nameInput.value})
      .then(data => {
        document.getElementById('results-table').style.display = ''
        removeResults('results')  // Remove to display a new one
        createRows(data);
      });
  }
})
