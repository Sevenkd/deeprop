var files = [];

$(function () {

    $("#inputFile").change(function () {
        files = this.files;
        console.log(files)

        // 检查文件长度, 一次性上传太多文件容易出问题
        let uploadFileLength = this.files.length;
        console.log(uploadFileLength);
        if (uploadFileLength > 1024) {
            alert("病例文件数量太多("+uploadFileLength+", 超过1024)，请分批次上传!");
            window.location.reload();
            return false;
        }

        // TODO: 用户选择上传文件后, 在这里做一些对文件的检测工作
        // 检查一下文件名是否安全, 统计每个病例中的文件内容, 显示统计信息
        // for循环遍历所有文件, 将待上传文件显示在表格中, 让用户可以选择删除不需要的文件
        // files[i]得到的文件是File类型, 应该可以预览内容
        // 后两项可以先缓缓

    });

    $("#submitBtn").click(function () {
        if (files.length == 0)
            alert("您还没有选择要上传的文件, 请选择文件后再上传!");

        var fd = new FormData();
        console.log(files.length);
        for (var i = 0; i < files.length; i++) {
            console.log(files[i])
            fd.append("dfile", files[i]);
        }
        console.log(fd);

        $.ajax({
            url: '/uploadInWeb',
            method: "post",
            data: fd,
            dataType: 'json',
            contentType: false,
            processData: false,
            cache: false,
            beforeSend: function () {
                //TODO: 显示进度条, 显示loading图标, 在上传前需要禁用上传按钮, 防止用户因页面没有反应而多次点击页面
                // 进度条通过下方xhr方法实现, 具体需要查一下资料, bootstrap有进度条相关的组件
                console.log("start uploading");
            },
            success: function (data) {
                console.log(data);
                if (data.res == 'success') {
                    // TODO: alert方法对用户来说不太友好, 找一套好看的信息显示组件, 用来显示后台信息
                    alert('上传完成');
                    for (let i = 0; i < data.uploadState.length; i++){
                        alert(data.uploadState[i])
                    }
                } else if (data.res == "unauthorized"){
                    // 用户未登录, 跳转到登录页面
                    alert("用户尚未登录, 请登录后重试!")
                    window.location.href = "/login?next=/"
                } else {
                    // 处理失败信息
                    alert("上传错误: " + data.desc)
                }
            },
            error: function () {
                alert("失败");
            },
            xhr: function(){
                  var xhr = new window.XMLHttpRequest();
                  //Download progress
                  console.log(xhr);
                  xhr.upload.addEventListener("progress", function(evt){
                      if (evt.lengthComputable) {
                         var percentComplete = (evt.loaded / evt.total) * 100 ;
                         var percentComplete_int = percentComplete && + percentComplete | 0 || 0;
                         //console.log(percentComplete_int);
                         // Do something with download progress
                         // console.log(percentComplete);
                         $("#_status").text(percentComplete_int + "%" )
                         $("#_progress").css({"width":percentComplete_int + "%","display":"inherit"})
                      }
                  }, false);
                  return xhr;
            }
        });
    });
})