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

document.getElementById('search').addEventListener('click', function () {
  const nameInput = document.getElementById('name')
  const name = nameInput.value
  if (!name.trim()) {
    document.getElementById('no-input-warning').hidden = false
  } else {
    postData('/search', {name: nameInput.value})
      .then(data => {
        document.getElementById('search-container').style.display = 'none'
        document.getElementById('results-table').style.display = ''
        createRows(data);
      });
  }
})
