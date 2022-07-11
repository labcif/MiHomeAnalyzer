def insert_html():
    return """
    <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" type="text/css" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
            <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.21/css/dataTables.bootstrap.min.css">
			<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/searchpanes/1.1.1/css/searchPanes.dataTables.min.css">
			<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/select/1.3.1/css/select.dataTables.min.css">
        </head>
        <body style="text-align:center">

            <h1>MiHome Analyzer detections report</h1>
            <div style="width:70%;margin-left:auto;margin-right:auto">
                <table id="example" class="table table-striped table-bordered" style="width:100%;border-radius:8px">
                </table>
            </div>

        </body>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>
	<script src="https://cdn.datatables.net/1.10.21/js/dataTables.bootstrap.min.js"></script>
	<script src="https://cdn.datatables.net/searchpanes/1.1.1/js/dataTables.searchPanes.min.js"></script>
	<script src="https://cdn.datatables.net/select/1.3.1/js/dataTables.select.min.js"></script>
    
    <script src="mihome_report_data.js"></script>
    <script>
            $(document).ready(function() {
                $('#example').DataTable( {
                    searchPanes:{
						layout: 'columns-1'
					},
					dom: 'Pfrtilp',
                    data: motions,
                    deferRender: true,
                    columns: [
                        { title: "Motion Date" },
                        { title: "Detection Path + Preview" },
                    ],
                    "columnDefs": [ 
                        {
                            "targets": [0],
                            "searchable": true,
                            "orderable": true,
                            searchPanes:{
                                show: true,
                            },
                        },
                        {
                            "targets" : [1],
                            "searchable": false,
                            "orderable": false,
                            "render" : function ( url) {
                                return url +'<video width="320" height="240" controls> <source src="' + url + '" type="video/mp4">Your browser does not support the video tag.</video>';
                            }
                        },
                    ]
                } );
            } );
    </script>
        </html>
"""