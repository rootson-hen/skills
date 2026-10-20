# When to Mock

Mock at **system boundaries** only:

- External APIs (payment, email, etc.)
- Databases (sometimes - prefer test DB)
- Time/randomness
- File system (sometimes)

Don't mock:

- Your own classes/modules
- Internal collaborators
- Anything you control

## Designing for Mockability

At system boundaries, design interfaces that are easy to mock:

**1. Use dependency injection**

Pass external dependencies in rather than creating them internally:

```java
// Easy to mock
class PaymentProcessor {
    private final PaymentClient paymentClient;

    PaymentProcessor(PaymentClient paymentClient) {
        this.paymentClient = paymentClient;
    }

    PaymentResult processPayment(Order order) {
        return paymentClient.charge(order.total());
    }
}

// Hard to mock (alternative implementation)
class PaymentProcessor {
    PaymentResult processPayment(Order order) {
        PaymentClient client = new StripeClient(System.getenv("STRIPE_KEY"));
        return client.charge(order.total());
    }
}
```

**2. Prefer SDK-style interfaces over generic fetchers**

Create specific functions for each external operation instead of one generic function with conditional logic:

```java
// GOOD: Each operation is independently mockable
interface UserApi {
    User getUser(String id);
    List<Order> getOrders(String userId);
    Order createOrder(CreateOrderRequest request);
}

// BAD: Mocking requires conditional logic inside the mock
interface Api {
    HttpResponse<String> fetch(String endpoint, RequestOptions options);
}
```

The SDK approach means:
- Each mock returns one specific shape
- No conditional logic in test setup
- Easier to see which endpoints a test exercises
- Type safety per endpoint
