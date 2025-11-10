// Sortable + summary helpers for Stats table
(function(){
  // --- existing sorter logic ---
  function parseValue(value, type){
    if(type === 'number'){
      var n = parseFloat(String(value).replace(/[^0-9.+-eE]/g, ''));
      return isNaN(n) ? 0 : n;
    }
    if(type === 'date'){
      var d = Date.parse(value);
      return isNaN(d) ? 0 : d;
    }
    return String(value).toLowerCase();
  }

  function sortTable(table, colIndex, type, asc){
    var tbody = table.tBodies[0];
    if(!tbody) return;
    var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
    rows.sort(function(a,b){
      var aText = (a.children[colIndex] && a.children[colIndex].textContent) || '';
      var bText = (b.children[colIndex] && b.children[colIndex].textContent) || '';
      var va = parseValue(aText.trim(), type);
      var vb = parseValue(bText.trim(), type);
      if(va < vb) return asc ? -1 : 1;
      if(va > vb) return asc ? 1 : -1;
      return 0;
    });
    var frag = document.createDocumentFragment();
    rows.forEach(function(r){ frag.appendChild(r); });
    tbody.appendChild(frag);
  }

  function makeSortable(table){
    var ths = table.tHead ? table.tHead.querySelectorAll('th') : [];
    if(!ths.length) return;
    Array.prototype.forEach.call(ths, function(th, i){
      var type = th.getAttribute('data-type') || 'string';
      var asc = true;
      th.style.cursor = 'pointer';
      th.addEventListener('click', function(){
        Array.prototype.forEach.call(th.parentNode.children, function(s){
          if(s !== th) s.removeAttribute('data-sort');
        });
        asc = ! (th.getAttribute('data-sort') === 'asc');
        th.setAttribute('data-sort', asc ? 'asc' : 'desc');
        sortTable(table, i, type, asc);
      });
    });
  }


  function setupTabs(){
    var snapTab = document.getElementById('snapshots-tab');
    var sessTab = document.getElementById('sessions-tab');
    var snapPanel = document.getElementById('snapshots-panel');
    var sessPanel = document.getElementById('sessions-panel');
    if(!snapTab || !sessTab || !snapPanel || !sessPanel) return;
    if(!snapTab._daTabAttached){
      snapTab._daTabAttached = true;
      snapTab.addEventListener('click', function(e){
        e.preventDefault();
        snapTab.classList.add('active');
        sessTab.classList.remove('active');
        snapPanel.style.display = '';
        sessPanel.style.display = 'none';
      });
    }
    if(!sessTab._daTabAttached){
      sessTab._daTabAttached = true;
      sessTab.addEventListener('click', function(e){
        e.preventDefault();
        sessTab.classList.add('active');
        snapTab.classList.remove('active');
        sessPanel.style.display = '';
        snapPanel.style.display = 'none';
      });
    }
  }

$(document).on('daPageLoad', function(){
    var tables = document.querySelectorAll('table.sortable');
    Array.prototype.forEach.call(tables, makeSortable);
    setupTabs();
});
})();
