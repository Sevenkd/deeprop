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

    $("div#mydropzone").dropzone({
        autoProcessQueue: true, //自动上传
        url: "/upload",//文件提交地址
        method:"post",  //也可用put
        paramName:"file", //默认为file
        maxFiles:10,//一次性上传的文件数量上限
        maxFilesize: 1024, //文件大小，单位：MB
        acceptedFiles: ".jpg,.gif,.png,.jpeg, .txt", //上传的类型
        uploadMultiple: true,
        addRemoveLinks:true,
        parallelUploads: 1,//一次上传的文件数量
        //previewsContainer:"#preview",//上传图片的预览窗口
        dictDefaultMessage:'拖动文件至此或者点击上传',
        dictMaxFilesExceeded: "您最多只能上传5个文件！",
        dictResponseError: '文件上传失败!',
        dictInvalidFileType: "文件类型只能是*.jpg,*.gif,*.png,*.jpeg。",
        dictFallbackMessage:"浏览器不受支持",
        dictFileTooBig:"文件过大上传文件最大支持.",
        dictRemoveLinks: "删除",
        dictCancelUpload: "取消",
        init:function(){
            this.on("addedfile", function(file) {
                //上传文件时触发的事件

            });
            this.on("success",function(file,data){


                //上传成功触发的事件
                console.log('ok');
//              angular.element(appElement).scope().file_id = data.data.id;

            });
            this.on("error",function (file,data) {
                //上传失败触发的事件
                console.log('fail');
                var message = '';
                //lavarel框架有一个表单验证，
                //对于ajax请求，JSON 响应会发送一个 422 HTTP 状态码，
                //对应file.accepted的值是false，在这里捕捉表单验证的错误提示
                if (file.accepted){
                    $.each(data,function (key,val) {
                        message = message + val[0] + ';';
                    })
                    //控制器层面的错误提示，file.accepted = true的时候；
                    alert(message);
                }
            });
            this.on("removedfile",function(file){
                //删除文件时触发的方法
//              var file_id = angular.element(appElement).scope().file_id;
//              if (file_id){
//                  $.post('/admin/del/'+ file_id,{'_method':'DELETE'},function (data) {
//                      console.log('删除结果:'+data.message);
//                  })
//              }
//              angular.element(appElement).scope().file_id = 0;
                document.querySelector('div .dz-default').style.display = 'block';
            });
        }


    })



});


