function isDuplicate(){
	var hash = {};
	for(var i=0; i<arguments.length; ++i){
		if (hash[arguments[i]] == true){
			return true;
		}
		hash[arguments[i]] = true;
	}
	return false;
}

function zip(){
	var n = arguments.length;
	var m = arguments[0].length;
	var result = [];
	for (var i=0; i<m; ++i){
		var tmp = [];
		for (var j=0; j<n; ++j){
			tmp.push(arguments[j][i]);
		}
		result.push(tmp);
	}
	return result;
}