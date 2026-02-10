use std::fs::File;
use std::io::{BufRead, BufReader};

pub fn replay_ws<F>(path: &str, mut handler: F)
where
    F: FnMut(serde_json::Value),
{
    let file = File::open(path).unwrap();
    for line in BufReader::new(file).lines() {
        let msg: serde_json::Value = serde_json::from_str(&line.unwrap()).unwrap();
        handler(msg);
    }
}
