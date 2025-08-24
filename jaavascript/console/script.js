//var: 함수레벨 스코프
//function func(){
//    if(true) {
//        var a = 'a';
//        console.log(a);
//    }
//    console.log(a);
//}

//func();

// let, const = block 레벨 스코프


function func(){
    if(true){
        let a = 'a';
        console.log(a);
    }
    console.log(a)
}
func();