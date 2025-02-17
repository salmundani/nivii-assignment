create table products (
    id SERIAL primary key,
    name varchar(255) not null
);

create table orders (
    id SERIAL primary key,
    ticket varchar(255) not null,
    datetime TIMESTAMP not null,
    waiter integer not null
);

create table order_product (
    id SERIAL primary key,
    product_id integer not null,
    order_id integer not null,
    quantity integer not null,
    price decimal(10, 2) not null,
    foreign key (product_id) references products(id),
    foreign key (order_id) references orders(id)
);
