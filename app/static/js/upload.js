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
        debugger;
        console.log(fd.length);
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
})

