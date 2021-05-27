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

function sanitize(name) {
  name = name.replace(/[0-9]/g, '')
  name = name.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
  name = name.replace(/[`~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/gi, '')
  return name.trim()
}

document.getElementById('search').addEventListener('click', function () {
  const noInputWarning = document.getElementById('no-input-warning')
  const nameInput = document.getElementById('name')
  let name = sanitize(nameInput.value)  // Get rid of accents, numbers and symbols
  if (!name) {
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
