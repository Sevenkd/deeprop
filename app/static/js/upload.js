var files=[];
$(function(){

    $("#inputFile").change(function(){
        files=this.files;
    });
    $("#submitBtn").click(function(){
        if(files.length == 0)
            alert("请添加文件");
        var fd = new FormData();
        console.log(files.length);
        debugger;
        for(var i = 0; i < files.length; i++){
            fd.append("dfile", files[i]);

        }
        $.ajax({
            url: 'http://192.168.7.181:9005/uploadInWeb',
            method: "post",
            data: fd,
            dataType: 'json',
            contentType: false,
            processData: false,
            cache: false,
            success: function(data){
                console.log(data);
                debugger;
                console.log("完成");
                if (data.res == 'success') {
                    alert('上传成功');
                }
                else {
                    alert("上传失败");
                }
            },
            error: function(){
                alert("失败");
            }
        });
    });

    $("div#dropzone").dropzone({
        url: "/file/post",
        paramName: "file", // The name that will be used to transfer the file
        maxFilesize: 2, // MB
        accept: function(file, done) {
            if (file.name === "dropzone.js") {
                alert("you can't!");
            }
            else { done(); }
        },
        maxFiles: 3,
        addRemoveLinks: true


    });



});

Dropzone.options.mydropzone = {
    paramName: "file", // The name that will be used to transfer the file
    maxFilesize: 2, // MB
    accept: function(file, done) {
        if (file.name === "dropzone.js") {
            done("Naha, you don't.");
        }
        else { done(); }
    }
};
