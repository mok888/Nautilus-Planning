pub fn hello_from_rust() -> String {
    "Hello from dinger-core!".to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        assert_eq!(hello_from_rust(), "Hello from dinger-core!");
    }
}
