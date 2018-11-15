<?php
header("Access-Control-Allow-Origin: *");
//ini_set('display_errors', '1');
require '/var/www/bin/dbconfig.php';
$mysql = XMLUtil::getDBConfiguration();

$dbname = "WEIBO";

// 设置返回json格式数据
header('content-type:application/json;charset=utf8');

$results = array();

//连接数据库
try {
    //$res = file_get_contents("php://input"); //取得json数据
    $res       = $_POST['data'];
    $operation = $_POST['operation'];
    $data      = json_decode($res, true); //格式化

    $conn = new PDO("mysql:host={$mysql['host']};dbname=$dbname;charset=utf8mb4", $mysql['user'], $mysql['password']);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $conn->beginTransaction();

    $sth = $conn->prepare("SELECT id FROM weibo_index WHERE id=:id");
    $sth->bindParam(':id', $data['status']['id']);
    $sth->execute();
    if ($sth->fetch()) {
        $results["errorCode"] = "101";
        $results["message"]   = "id is exist.";
    } else {

        $created_at   = date('Y-m-d H:i:s', strtotime($data['status']['created_at']));
        $retweeted_id = null;
        $pic_ids      = null;
        $page_info    = null;

        if (isset($data['status']['pic_ids'])) {
            $pic_ids = json_encode($data['status']['pic_ids']);
        }

        if (isset($data['status']['page_info'])) {
            $page_info = json_encode($data['status']['page_info'], JSON_UNESCAPED_UNICODE);
        }

        if (isset($data['status']['retweeted_status'])) {
            $retweeted_id = $data['status']['retweeted_status']['id'];
        }

        if ($operation == 'update') {
            $sql = "UPDATE weibo_index SET text=:text , user_screen_name=:user_screen_name , reposts_count=:reposts_count , comments_count=:comments_count , attitudes_count=:attitudes_count , original_data=:original_data , pic_ids=:pic_ids, page_info=:page_info, edit_count=:edit_count WHERE id=:id";
            $sth = $conn->prepare($sql);
            $sth->bindParam(':edit_count', $data['status']['edit_count']);
        } else {
            $sql = "INSERT INTO weibo_index (id , created_at , text , user_id , user_screen_name , reposts_count , comments_count , attitudes_count , bid , original_data , retweeted_id , pic_ids, page_info) VALUES (:id , :created_at , :text , :user_id , :user_screen_name , :reposts_count , :comments_count , :attitudes_count , :bid , :original_data , :retweeted_id , :pic_ids , :page_info)";
            $sth = $conn->prepare($sql);

            $sth->bindParam(':created_at', $created_at);
            $sth->bindParam(':retweeted_id', $retweeted_id);

            $sth->bindParam(':user_id', $data['status']['user']['id']);
            $sth->bindParam(':bid', $data['status']['bid']);
        }

        $sth->bindParam(':pic_ids', $pic_ids);
        $sth->bindParam(':page_info', $page_info);
        $sth->bindParam(':id', $data['status']['id']);
        $sth->bindParam(':text', $data['status']['text']);
        $sth->bindParam(':user_screen_name', $data['status']['user']['screen_name']);
        $sth->bindParam(':reposts_count', $data['status']['reposts_count']);
        $sth->bindParam(':comments_count', $data['status']['comments_count']);
        $sth->bindParam(':attitudes_count', $data['status']['attitudes_count']);
        $sth->bindParam(':original_data', $res);
        $sth->execute();

        if (isset($data['status']['pics'])) {
            $sth_pic = $conn->prepare("SELECT pid FROM weibo_pic WHERE pid=:pid");
            $sth_pic->bindParam(':pid', $pid);

            $sth_pic_ins = $conn->prepare("INSERT INTO weibo_pic (pid , type , mid) VALUES (:pid , :type , :mid)");
            $sth_pic_ins->bindParam(':pid', $pid);
            $sth_pic_ins->bindParam(':type', $type);
            $sth_pic_ins->bindParam(':mid', $data['status']['id']);

            $sth_orj_ins = $conn->prepare("INSERT INTO weibo_pic_orj360 (pid , width , height , croped , url) VALUES (:pid , :width , :height , :croped , :url)");
            $sth_orj_ins->bindParam(':pid', $pid);
            $sth_orj_ins->bindParam(':width', $orj_width);
            $sth_orj_ins->bindParam(':height', $orj_height);
            $sth_orj_ins->bindParam(':croped', $orj_croped);
            $sth_orj_ins->bindParam(':url', $orj_url);

            $sth_lar_ins = $conn->prepare("INSERT INTO weibo_pic_large (pid , width , height , croped , url) VALUES (:pid , :width , :height , :croped , :url)");
            $sth_lar_ins->bindParam(':pid', $pid);
            $sth_lar_ins->bindParam(':width', $lar_width);
            $sth_lar_ins->bindParam(':height', $lar_height);
            $sth_lar_ins->bindParam(':croped', $lar_croped);
            $sth_lar_ins->bindParam(':url', $lar_url);

            foreach ($data['status']['pics'] as $pic) {
                $pid = $pic['pid'];
                $sth_pic->execute();
                if (!$sth_pic->fetch()) {
                    $type = substr(strrchr($pic['url'], '.'), 1);
                    $sth_pic_ins->execute();
                    $orj_width  = $pic['geo']['width'];
                    $orj_height = (int) $pic['geo']['height'];
                    $orj_croped = $pic['geo']['croped'];
                    $orj_url    = $pic['url'];
                    if ($orj_height > 1200) {
                        $orj_height = 1200;
                    }

                    $lar_width  = $pic['large']['geo']['width'];
                    $lar_height = $pic['large']['geo']['height'];
                    $lar_croped = $pic['large']['geo']['croped'];
                    $lar_url    = $pic['large']['url'];
                    $sth_orj_ins->execute();
                    $sth_lar_ins->execute();
                    //exec("python /var/www/bin/download_pic.py " . escapeshellarg($pic['pid'] . "." . $type) . " >/dev/null &");
                }
            }
        }
        $conn->commit();

        $results["errorCode"] = "0";
        $results["message"]   = "ok";
    }
} catch (PDOException $e) {
    $conn->rollBack();
    $results["errorCode"] = "200";
    $results["message"]   = $e->getMessage();
}
echo json_encode($results);
$conn = null;
