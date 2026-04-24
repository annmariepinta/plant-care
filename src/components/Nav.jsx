import logo from '../assets/Logo.svg'
import { Link, NavLink } from 'react-router-dom';
import { useState } from 'react';


const Nav = () => {

    const [isOpen, setIsOpen] = useState(false);

    const navLinkStyle = ({ isActive }) => {
        return {
            color: isActive ? "black" : "#767676",
        };
    };
    const toggleNavMenu = () => {
        setIsOpen(!isOpen);
    };
    const toggleMenu = () => {
        window.scroll(0, 0);
        setIsOpen(!isOpen);
    };
    return (<>
        <div className="py-[16px] lg:py-[28px] px-[20px] lg:px-[120px] flex justify-between items-center w-[100vw] overflow-x-hidden">
            <Link to={'/'} className='hidden lg:block'>
                <img src={logo} alt="Tomato Planet" className="h-[44px] w-auto" />
            </Link>

            <div className='hidden lg:block'>
                <div className='flex justify-end items-center gap-[56px] text-[18px]'>
                    <NavLink to={'/'} style={navLinkStyle}
                    >Home</NavLink>
                    <NavLink to={'/detect'} style={navLinkStyle}
                    >Analyze</NavLink>
                    <NavLink to={'/about'} style={navLinkStyle}
                    >About Us</NavLink>
                    <NavLink to={'/contact'} style={navLinkStyle}
                    >Contact Us</NavLink>
                </div>
            </div>

            <div
                className="lg:hidden flex justify-between items-center w-[100vw] px-[5px] py-2 z-50"
                onClick={toggleNavMenu}
            >
                <img src={logo} alt="logo" className="w-[100px]" />
                <div></div>
                <div
                    className={` hamburger-menu z-50 pr-3 ${isOpen ? "open" : ""} ${isOpen ? "flex-row-reverse rounded-r-[20px]" : ""
                        }`}
                >
                    <div
                        className={`line ${!isOpen ? `bg-primary mb-3` : `bg-primary`}`}
                    ></div>
                    <div className={`line bg-primary hidden`}></div>
                    <div className={`line ${!isOpen ? `bg-primary` : `bg-primary`}`}></div>
                </div>
            </div>

            <div
                className={`${isOpen
                    ? "fixed bg-white top-0 right-0 left-0 w-[100vw] flex-col transition-all duration-300 ease-in-out px-[24px] flex justify-between gap-[25px] h-[100vh] text-primary lg:hidden"
                    : "fixed top-[-600%] transition-all duration-300 ease-in-out"
                    } `}
            >
                <div className="flex justify-center items-center h-full">
                    <div className="text-center flex flex-col justify-center items-center h-full gap-[0px] text-[40px] font-[600]">
                        <NavLink style={navLinkStyle} onClick={toggleMenu} to={"/"} className="w-full">
                            <p className="">Home</p>
                        </NavLink>
                        <NavLink style={navLinkStyle} onClick={toggleMenu} to={"/detect"} className="w-full">
                            <p className="">Analyze</p>
                        </NavLink>
                        <NavLink style={navLinkStyle} onClick={toggleMenu} to={"/about"} className="w-full">
                            <p className="">About</p>
                        </NavLink>
                        <NavLink style={navLinkStyle} onClick={toggleMenu} to={"/contact"} className="w-full">
                            <p className="">Contact</p>
                        </NavLink>
                    </div>
                </div>
            </div>
        </div>
    </>);
}

export default Nav;