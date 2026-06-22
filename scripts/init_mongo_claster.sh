#!/bin/sh

docker exec mongocfg1 mongosh --eval '
rs.initiate({
  _id: "mongors1conf",
  configsvr: true,
  members: [
    {_id: 0, host: "mongocfg1:27017"},
    {_id: 1, host: "mongocfg2:27017"},
    {_id: 2, host: "mongocfg3:27017"}
  ]
})
'

docker exec mongors1n1 mongosh --eval '
rs.initiate({
  _id: "mongors1",
  members: [
    {_id: 0, host: "mongors1n1:27017"},
    {_id: 1, host: "mongors1n2:27017"},
    {_id: 2, host: "mongors1n3:27017"}
  ]
})
'

docker exec mongors2n1 mongosh --eval '
rs.initiate({
  _id: "mongors2",
  members: [
    {_id: 0, host: "mongors2n1:27017"},
    {_id: 1, host: "mongors2n2:27017"},
    {_id: 2, host: "mongors2n3:27017"}
  ]
})
'

docker exec mongos1 mongosh --eval '
sh.addShard("mongors1/mongors1n1:27017,mongors1n2:27017,mongors1n3:27017")
'

docker exec mongos1 mongosh --eval '
sh.addShard("mongors2/mongors2n1:27017,mongors2n2:27017,mongors2n3:27017")
'

docker exec mongos1 mongosh --eval '
sh.enableSharding("ugc")
'

docker exec mongos1 mongosh --eval '
sh.status()
'