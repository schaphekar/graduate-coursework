package visitor;

public interface IComposite {
    int accept(IVisitor sumVisitor);
}
