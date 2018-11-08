<?php
header("Access-Control-Allow-Origin: *");
//ini_set('display_errors', '1');
require '/var/www/bin/dbconfig.php';
$mysql = XMLUtil::getDBConfiguration();

$hostname = "";
$dbname = "WEIBO";

// 设置返回json格式数据
header('content-type:application/json;charset=utf8');

// 获取分页参数
$page = 1 ;
$pageSize = 10;
empty($_GET["page"]) || $page = (int)$_GET["page"];
empty($_GET["pageSize"]) || $pageSize = (int)$_GET["pageSize"];

$con_arr = array();
empty($_GET["user_id"]) || $con_arr[] = "c.user_id=:user_id";
empty($_GET["begin_date"]) || $con_arr[] = "c.created_at>=:begin_date";
empty($_GET["end_date"]) || $con_arr[] = "c.created_at<=:end_date";
$con_str = empty($con_arr) ? "" : "WHERE " . implode(" AND ",$con_arr);

//连接数据库
try {
    $conn = new PDO("mysql:host={$mysql['host']};dbname=$dbname;charset=utf8mb4", $mysql['user'], $mysql['password']);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $sql = "SELECT a.pid,a.type,b.width,b.height,c.user_screen_name,c.user_id,c.text,c.created_at FROM weibo_pic a JOIN weibo_pic_orj360 b JOIN weibo_index c ON a.pid=b.pid AND a.mid=c.id {$con_str} ORDER BY c.id DESC LIMIT :offset , :length ";
    $stmt = $conn->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY)); 
    empty($_GET["user_id"]) || $stmt->bindParam(':user_id',$_GET["user_id"]);
    empty($_GET["begin_date"]) || $stmt->bindParam(':begin_date',$_GET["begin_date"]);
    empty($_GET["end_date"]) || $stmt->bindParam(':end_date',$_GET["end_date"]);
    $stmt->bindValue(':offset',($page-1)*$pageSize, PDO::PARAM_INT);
    $stmt->bindValue(':length',$pageSize, PDO::PARAM_INT);
    $stmt->execute();
 
    // 设置结果集为关联数组
    $stmt->setFetchMode(PDO::FETCH_ASSOC); 
    $results = array();
    while ($row = $stmt->fetch()) {
      $row['large_url'] = $hostname . "/weibo/image/large/" . $row['pid'] . '.' . $row['type'];
      $row['orj360_url'] = $hostname . "/weibo/image/orj360/" . $row['pid'] . '.' . $row['type'];
      $row['username']=$row['user_screen_name'];
      unset($row['user_screen_name']);
      $results[] = $row;
    }
    // 将数组转成json格式
    echo json_encode($results);
}
catch(PDOException $e) {
    echo "Error: " . $e->getMessage();
}
$conn = null;
?>
