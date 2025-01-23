function copy_link(link) {
    navigator.clipboard.writeText(link).then(function() {
        alert("Link copiato negli appunti");
    }, function() {
        alert("Errore nel copiare il link");
    });
}